from settings import get_settings

settings = get_settings()


def main():
    print(f"index={settings.aws_batch_job_array_index}")


if __name__ == "__main__":
    main()
