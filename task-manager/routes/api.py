from flask import Blueprint, jsonify, request
from services.tasks import (get_task, create_task, process_order, update_task_priority,
                            get_all_tasks, get_tasks_by_priority)
from services.users import get_user, get_notification_pref, set_notification_pref
from utils.errors import AppError, ValidationError

api = Blueprint("api", __name__)

@api.errorhandler(AppError)
def handle_app_error(e):
    return jsonify({"error": e.message}), e.status_code

@api.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_route(task_id):
    return jsonify(get_task(task_id))

@api.route("/tasks", methods=["POST"])
def create_task_route():
    data = request.get_json()
    return jsonify(create_task(data["title"], data["user_id"])), 201

@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    if "priority" not in request.args:
        return jsonify(get_all_tasks())
    priority = request.args.get("priority", type=int)
    return jsonify(get_tasks_by_priority(priority))

@api.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_priority_route(task_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("body", "must be a JSON object")
    return jsonify(update_task_priority(task_id, data.get("priority")))

@api.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    return jsonify(get_user(user_id))

@api.route("/users/<int:user_id>/notifications", methods=["PATCH"])
def set_notification_pref_route(user_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("body", "must be a JSON object")
    return jsonify(set_notification_pref(user_id, data.get("notification_pref")))

@api.route("/users/<int:user_id>/notifications", methods=["GET"])
def get_notification_pref_route(user_id):
    return jsonify({"notification_pref": get_notification_pref(user_id)})
