import config
import sqlite3
from config import CNT_LETTERS
from flask import Flask, jsonify, request, make_response, abort
from flask import render_template, json

conn = sqlite3.connect("app.db", check_same_thread=False)
cursor = conn.cursor()

app = Flask(__name__)


def check_note(note):
    return note.get("content")


@app.route("/notes", methods=["POST"])
def notes():
    if not request.json:
        return make_response("Пустой запрос", 400)
    note = request.json
    if not check_note(note):
        return make_response("Не указано обязательное поле - content", 400)

    cursor.execute("""
        INSERT INTO note("title", "content")
        VALUES(?, ?)
    """, (note.get("title"), note.get("content")))
    conn.commit()
    last_id = cursor.lastrowid
    cursor.execute("""
        SELECT * FROM note WHERE id = ?
    """, (last_id,))
    data = cursor.fetchone()

    return make_response(jsonify({
        "id": data[0],
        "title": data[1],
        "content": data[2]
    }), 201)


@app.route("/notes", methods=["GET"])
def all_notes():
    query = request.args.get("query")
    where = ""
    if query:
        where = "WHERE lower(title) LIKE lower('{0}') or lower(content) LIKE lower('{0}')".format("%" + query + "%")
    cursor.execute("""
        SELECT id, IFNULL(title, substr(content, 0, ?)), content
        FROM note
        {where}
    """.format(where=where), (CNT_LETTERS + 1,))
    notes = cursor.fetchall()
    response = []
    for note in notes:
        response.append({
            "id": note[0],
            "title": note[1],
            "content": note[2]
        })
    return make_response(jsonify(response), 200)


@app.route("/notes/<id>", methods=["GET"])
def one_note(id):
    cursor.execute("""
        SELECT id, IFNULL(title, substr(content, 0, ?)), content
        FROM note
        WHERE id = ?
    """, (CNT_LETTERS + 1, id))
    note = cursor.fetchone()
    if not note:
        return make_response(jsonify({}), 200)
    return make_response(jsonify({
        "id": note[0],
        "title": note[1],
        "content": note[2]
    }), 200)


@app.route("/notes/<id>", methods=["PUT"])
def edit_note(id):
    if not request.json:
        return make_response("Пустой запрос", 400)
    edit = request.json

    if "title" in edit:
        cursor.execute("""
            UPDATE note
            SET title = ?
            WHERE id = ?
        """, (edit["title"], id))
    if "content" in edit:
        cursor.execute("""
            UPDATE note
            SET content = ?
            WHERE id = ?
        """, (edit["content"], id))
    conn.commit()
    return make_response(jsonify({}), 200)


@app.route("/notes/<id>", methods=["DELETE"])
def del_note(id):
    cursor.execute("""
        DELETE FROM note
        WHERE id = ?
    """, (id))
    conn.commit()
    return make_response(jsonify({}), 200)


if __name__ == "__main__":
    # Выполняется дважды из-за дебаг мода
    app.run(debug=True)
