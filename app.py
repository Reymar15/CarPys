from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    cars = [
        {
            "name": "Range Rover Sport",
            "price": "$95/day",
            "image": "https://images.unsplash.com/photo-1503376780353-7e6692767b70"
        },
        {
            "name": "BMW M4 Coupe",
            "price": "$120/day",
            "image": "https://images.unsplash.com/photo-1511919884226-fd3cad34687c"
        },
        {
            "name": "Ferrari 488",
            "price": "$450/day",
            "image": "https://images.unsplash.com/photo-1502877338535-766e1452684a"
        }
    ]
    return render_template("index.html", cars=cars)

if __name__ == "__main__":
    app.run()