from app.database.models.ball_by_ball import (
    BallByBall
)


class BallService:

    @staticmethod
    def bulk_insert_balls(
        db,
        balls_data: list
    ):

        objects = []

        for ball in balls_data:

            obj = BallByBall(**ball)

            objects.append(obj)

        db.bulk_save_objects(objects)

        db.commit()

        return len(objects)