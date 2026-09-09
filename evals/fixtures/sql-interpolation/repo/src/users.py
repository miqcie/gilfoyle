def find_user(db, user_id):
    return db.execute(f"SELECT * FROM users WHERE id = {user_id}").fetchone()
