from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import models


class Database:

    def __init__(self, db_url):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.maker = sessionmaker(bind=engine)

    def get_or_create(self, session, model, filter_field, data):
        instance = session.query(model).filter_by(**{filter_field: data[filter_field]}).first() # all(). order.all()
        if not instance:
            instance = model(**data)

        return instance

    def create_comments(self, post_id, data):
        # создаем сессию
        session = self.maker()
        # извлекаем комментарии, пока не закончатся
        while True:
            try:
                comment = data.pop(0)
            except IndexError:
                break
            # подготавливаем сущеность author для занесения в бд,
            # для этого проверяем автора комментария есть он уже в бд или нет
            author = self.get_or_create(
                session,
                models.Author,
                "url",
                dict(
                    name=comment["comment"]["user"]["full_name"],
                    url=comment["comment"]["user"]["url"],
                    gb_id=comment["comment"]["user"]["id"]),
            )
            if not author.gb_id:
                author.gb_id = comment["comment"]["user"]["id"]
            # готовим коммент для заносения в бд, проверив, есть он уже или нет
            comment_db = self.get_or_create(
                session, models.Comment, "id", comment["comment"],
            )
            comment_db.author = author
            comment_db.post_id = post_id
            # подготавливаем транзакцию
            session.add(comment_db)
            # пытаемся зафиксировать транзакцию
            try:
                session.commit()
            except Exception:
                session.rollback()
            if comment["comment"]["children"]:
                data.extend(comment["comment"]["children"])
        # закрываем сессию
        session.close()

    def add_post(self, data):
        # создаем сессию
        session = self.maker()
        # готовим запись с информацией о посте, проверив - есть ли уже такой в базе или нет
        post = self.get_or_create(session, models.Post, "id", data["post_data"])
        # готовим запись с информацией об авторе, проверив - есть ли уже такой в базе или нет
        author = self.get_or_create(session, models.Author, "url", data['author_data'])
        # связываем пост и его автора
        post.author = author
        # готовим запись о тегах, проверив есть уже такие в базе или нет и связываем с постом
        post.tags.extend(map(
            lambda tag_data: self.get_or_create(session, models.Tag, "url", tag_data),
            data["tags_data"],
        ))
        # готовим транзакцию вставки записей о посте в таблице Post и связанных с ней Author и Tag
        session.add(post)
        # пытаемся зафксировать транзакцию
        try:
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
        # Заносим информацию о комментах к посту в бд
        self.create_comments(data["post_data"]["id"], data['comments_data'])
