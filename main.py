from flask import Flask, render_template, request, redirect, url_for, make_response
import requests
from datetime import datetime
from auth import get_current_user
from database import SessionLocal, get_db
from models import RenovationPackage

# URL FastAPI
FASTAPI_URL = "http://127.0.0.1:8000/api/"

# Инициализация Flask-приложения
flask_app = Flask(__name__)

@flask_app.route("/", methods=["GET", "POST"])
def index():
    user_data = None
    message = ""

    if request.method == "POST":
        user_id = request.form.get("user_id")

        if user_id:
            try:
                # Отправляем запрос к FastAPI для получения данных пользователя
                response = requests.get(f"http://127.0.0.1:8000/api/users/{user_id}")
                if response.status_code == 200:
                    user_data = response.json()
                    if "message" in user_data:
                        message = user_data["message"]
                else:
                    message = "Ошибка при запросе данных."
            except Exception as e:
                message = f"Ошибка соединения: {e}"

    return render_template("index.html", user_data=user_data, message=message)

@flask_app.route("/about")
def about_us():
    return render_template("about_us.html")

@flask_app.route('/catalog', methods=['GET'])
def catalog():
    db = SessionLocal()
    packages = db.query(RenovationPackage).all()
    db.close()
    return render_template('catalog.html', packages=packages)


@flask_app.route("/register", methods=["GET", "POST"])
def register():
    message = "Register"
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        # Собираем данные в формате JSON
        data = {"name": name, "email": email, "password": password}

        # Отправляем запрос с JSON-данными
        response = requests.post("http://127.0.0.1:8000/api/register/", json=data)
        if response.status_code == 200:
            return redirect(url_for("login"))
        else:
            message = response.json().get("detail", "An error occurred")

    return render_template("register.html", message=message)


@flask_app.route("/login", methods=["GET", "POST"])
def login():
    message = "login br"
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        data = {"email": email, "password": password}

        response = requests.post(f"http://127.0.0.1:8000/api/login/", json=data)
        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get("access_token")  # Получаем токен
            if access_token:
                # Создаем ответ с перенаправлением на страницу профиля
                resp = make_response(redirect("/profile_page"))
                resp.set_cookie("access_token", access_token, httponly=True)  # Сохраняем токен в cookie
                return resp
            else:
                message = "Access token not found in response."
        else:
            message = response.json().get("detail", "An error occurred")
    return render_template("admin_catalog.html", message=message)

@flask_app.route('/about_package/<int:package_id>', methods=['GET'])
def about_package(package_id):
    db = SessionLocal()
    package = db.query(RenovationPackage).filter(RenovationPackage.id == package_id).first()
    db.close()
    if not package:
        return "Package not found", 404
    return render_template('about_package.html', package=package)


@flask_app.route("/profile_page")
def profile_page():
    # Получаем токен из cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        return redirect("/login")  # Если токена нет, перенаправляем на страницу логина

    # Получаем информацию о пользователе с FastAPI
    response = requests.get(
        "http://127.0.0.1:8000/profile",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code == 200:
        user_data = response.json()  # Данные о пользователе из FastAPI
        return render_template("profile.html", user=user_data)  # Передаем данные о пользователе в шаблон
    else:
        return redirect("/login")  # Если не удалось получить данные о пользователе, редиректим на страницу логина



@flask_app.route("/delete_profile", methods=["POST"])
def delete_profile_page():
    response = requests.delete("http://127.0.0.1:8000/profile", headers={"Authorization": f"Bearer {request.cookies.get('access_token')}"})
    if response.status_code == 200:
        return render_template("index.html", message="Profile deleted successfully!")
    else:
        return render_template("profile.html", message=response.json().get("detail", "Error occurred"))


@flask_app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile_page():
    message = ""
    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "password": request.form.get("password")
        }
        response = requests.put(
            "http://127.0.0.1:8000/profile",
            json=data,
            headers={"Authorization": f"Bearer {request.cookies.get('access_token')}"}
        )
        if response.status_code == 200:
            return redirect("/profile_page")
        else:
            message = response.json().get("detail", "Error occurred")
    return render_template("edit_profile.html", message=message)

from flask import render_template, redirect, url_for, request
from auth import get_current_user

@flask_app.route('/admin/catalog', methods=['GET', 'POST'])
def admin_catalog():
    # Проверяем, что текущий пользователь — админ
    access_token = request.cookies.get("access_token")
    if not access_token:
        return redirect("/login")

    response = requests.get(
        "http://127.0.0.1:8000/profile",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code != 200:
        return redirect("/login")

    user_data = response.json()
    if user_data['role'] != 'admin':
        return redirect('/catalog')  # Перенаправляем обычных пользователей в общий каталог

    # Получаем список пакетов
    db = SessionLocal()
    packages = db.query(RenovationPackage).all()
    db.close()

    return render_template('admin_catalog.html', packages=packages)


@flask_app.route('/admin/create_package', methods=['GET', 'POST'])
def create_package():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        photo_url = request.form['photo_url']

        db = SessionLocal()
        new_package = RenovationPackage(
            name=name, description=description, price=price, photo_url=photo_url
        )
        db.add(new_package)
        db.commit()
        db.close()
        return redirect('/admin/catalog')

    return render_template('create_package.html')

@flask_app.route('/admin/edit_package/<int:package_id>', methods=['GET', 'POST'])
def edit_package(package_id):
    db = SessionLocal()
    package = db.query(RenovationPackage).get(package_id)

    if request.method == 'POST':
        package.name = request.form['name']
        package.description = request.form['description']
        package.price = float(request.form['price'])
        package.photo_url = request.form['photo_url']
        db.commit()
        db.close()
        return redirect('/admin/catalog')

    db.close()
    return render_template('edit_package.html', package=package)

@flask_app.route('/admin/delete_package/<int:package_id>', methods=['POST'])
def delete_package(package_id):
    db = SessionLocal()
    package = db.query(RenovationPackage).get(package_id)
    db.delete(package)
    db.commit()
    db.close()
    return redirect('/admin/catalog')


@flask_app.route("/admin/packages")
def admin_packages():
    current_user = get_current_user()
    if current_user.role != "admin":
        return redirect(url_for("catalog"))

    db = next(get_db())
    packages = db.query(RenovationPackage).all()
    return render_template("admin_packages.html", packages=packages)


@flask_app.route("/admin/packages/new")
def add_package():
    current_user = get_current_user()
    if current_user.role != "admin":
        return redirect(url_for("login"))
    return render_template("add_package.html")







if __name__ == "__main__":
    flask_app.run(debug=True, port=5000)
