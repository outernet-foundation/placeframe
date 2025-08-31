from settings import get_settings

settings = get_settings()


def main():
    print(f"index={settings.batch_job_array_index}")


if __name__ == "__main__":
    main()
