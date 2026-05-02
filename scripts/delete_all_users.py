import argparse
import asyncio
import sys
from pathlib import Path
from sqlalchemy import func, select, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.session import SessionLocal
from models.user import User


async def delete_all_users(confirm: bool) -> None:
    async with SessionLocal() as session:
        before_count = await session.scalar(select(func.count(User.id)))
        before_count = int(before_count or 0)

        if before_count == 0:
            print("No users found. Nothing to delete.")
            return

        if not confirm:
            print(
                f"Found {before_count} users. Re-run with --yes to delete all users."
            )
            return

        try:
            dialect_name = session.get_bind().dialect.name

            if dialect_name == "postgresql":
                await session.execute(text("TRUNCATE TABLE users CASCADE;"))
            else:
                users = (await session.execute(select(User))).scalars().all()
                for user in users:
                    session.delete(user)

            await session.commit()

            after_count = await session.scalar(select(func.count(User.id)))
            after_count = int(after_count or 0)

            deleted_count = before_count - after_count
            print(f"Deleted {deleted_count} users.")
            print(f"Remaining users: {after_count}")
        except Exception:
            await session.rollback()
            raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete all users from the database used by this project."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually perform deletion. Without this flag, script is a dry run.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(delete_all_users(confirm=args.yes))
