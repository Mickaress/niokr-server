from flask import Flask
from flask_jwt_extended import JWTManager
from project.routes import project
from skill.routes import skill
from user.routes import user
from vacancy.routes import vacancy

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
jwt = JWTManager(app)

app.register_blueprint(project)
app.register_blueprint(skill)
app.register_blueprint(user)
app.register_blueprint(vacancy)


if __name__ == '__main__':
    app.run(debug=True)
