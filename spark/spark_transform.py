"""
Spark Structured Streaming job: consumes raw job postings from Kafka,
applies transformations and data quality checks, and lands curated
Parquet files that the Snowflake loader picks up next.

Run with trigger=AvailableNow so it drains whatever is currently on the
topic and exits - this lets Airflow schedule it as a normal batch task
instead of running a 24/7 streaming job.

    spark-submit \
        --master spark://spark-master:7077 \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
        streaming/spark_transform.py
"""
import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    LongType,
    StringType,
    StructField,
    StructType,
)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_JOBS_TOPIC", "jobs.raw")
PROCESSED_PATH = os.getenv("PROCESSED_PATH", "/opt/project/data/processed/jobs")
REJECTED_PATH = os.getenv("REJECTED_PATH", "/opt/project/data/processed/_rejected/jobs")
CHECKPOINT_PATH = os.getenv("CHECKPOINT_PATH", "/opt/project/data/checkpoints/jobs_transform")

RAW_SCHEMA = StructType(
    [
        StructField("id", StringType()),
        StructField("company", StringType()),
        StructField("position", StringType()),
        StructField("location", StringType()),
        StructField("salary", StringType()),
        StructField("salary_min", LongType()),
        StructField("salary_max", LongType()),
        StructField("date", StringType()),
        StructField("tags", ArrayType(StringType())),
        StructField("url", StringType()),
        StructField("apply_url", StringType()),
        StructField("description", StringType()),
        StructField("_ingested_at", StringType()),
    ]
)


def build_spark_session() -> SparkSession:
    return (
        SparkSession.builder.appName("job-market-intelligence-transform")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def read_raw_stream(spark: SparkSession):
    return (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )


def parse_and_transform(raw_df):
    parsed = raw_df.select(
        F.col("key").cast("string").alias("kafka_key"),
        F.from_json(F.col("value").cast("string"), RAW_SCHEMA).alias("data"),
    ).select("kafka_key", "data.*")

    return (
        parsed
        # normalize/derive fields
        .withColumn("job_id", F.coalesce(F.col("id"), F.col("kafka_key")))
        .withColumn("company", F.trim(F.col("company")))
        .withColumn("position", F.trim(F.col("position")))
        .withColumn("location", F.when(F.trim(F.col("location")) == "", None).otherwise(F.trim(F.col("location"))))
        .withColumn(
            "date_posted",
            F.coalesce(F.to_date(F.col("date")), F.to_date(F.col("_ingested_at"))),
        )
        .withColumn("ingestion_date", F.to_date(F.col("_ingested_at")))
        .withColumn("tags", F.coalesce(F.col("tags"), F.array()))
        .withColumn(
            "salary_min",
            F.coalesce(F.col("salary_min"), F.regexp_extract(F.col("salary"), r"(\d[\d,]*)", 1).cast("long")),
        )
        .withColumn("salary_max", F.coalesce(F.col("salary_max"), F.col("salary_min")))
        .drop("id", "kafka_key")
    )


def split_by_data_quality(transformed_df):
    """A record is 'good' only if it has the minimum fields a curated job
    posting needs. Everything else goes to the rejected path so bad data
    is visible instead of silently vanishing."""
    dq_checks = (
        F.col("job_id").isNotNull()
        & F.col("company").isNotNull()
        & (F.col("company") != "")
        & F.col("position").isNotNull()
        & (F.col("position") != "")
    )

    deduped = transformed_df.dropDuplicates(["job_id"])

    good_df = deduped.filter(dq_checks)
    rejected_df = deduped.filter(~dq_checks).withColumn("rejection_reason", F.lit("missing_required_field"))

    return good_df, rejected_df


def process_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        print(f"[batch {batch_id}] no records")
        return

    good_df, rejected_df = split_by_data_quality(batch_df)

    good_count = good_df.count()
    rejected_count = rejected_df.count()

    if good_count > 0:
        good_df.write.mode("append").partitionBy("ingestion_date").parquet(PROCESSED_PATH)

    if rejected_count > 0:
        rejected_df.write.mode("append").partitionBy("ingestion_date").parquet(REJECTED_PATH)

    print(f"[batch {batch_id}] good={good_count} rejected={rejected_count}")


def main():
    spark = build_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    raw_df = read_raw_stream(spark)
    transformed_df = parse_and_transform(raw_df)

    query = (
        transformed_df.writeStream.foreachBatch(process_batch)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .trigger(availableNow=True)
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
