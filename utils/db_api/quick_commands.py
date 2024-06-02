from data.config import POSTGRES_URL
from utils.db_api.db_gino import db
from sqlalchemy import create_engine, select, text, func

engine = create_engine(POSTGRES_URL)
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

async def get_task_data(chat_id):
    # Выполнение запроса
    stmt = text(
        """
        SELECT DISTINCT
            t.created_at AS "Дата создания",
            t.updated_at AS "Дата изменения",
            t.created_by AS "Создал",
            uc.t_username AS "Создал (username)",
            uc.t_fullname AS "Создал (fullname)",
            uc.t_url AS "Создал (url)",
            t.deadline AS "Срок",
            t.name AS "Название задачи",
            t.description AS "Описание задачи",
            t.responsible AS "Ответственный",
            t.status AS "Статус",
            t.decision_by_close AS "Решение",
            t.closed_at AS "Дата закрытия",
            t.closed_by AS "Закрыл",
            uz.t_username AS "Закрыл (username)",
            uz.t_fullname AS "Закрыл (fullname)",
            uz.t_url AS "Закрыл (url)"
        FROM
            tasks t
        LEFT JOIN
            users uc ON t.created_by = uc.user_id
        LEFT JOIN
            users uz ON t.closed_by = uz.user_id
        WHERE
            t.chat_id = :chat_id
        ORDER BY
            t.deadline ASC;
        """
    )


    results = session.execute(stmt, {"chat_id": chat_id})
    rows = results.fetchall()
    return rows