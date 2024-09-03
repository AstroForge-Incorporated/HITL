from pywebio import start_server
from pywebio.output import put_html

IP = "192.168.80.85"

def show_dashboard():
    put_html('''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=New+Amsterdam&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Jersey:wght@400&display=swap');

        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            width: 100%;
            font-family: 'Roboto', sans-serif;
            background-color: #3e3f43;
            color: #FFFFFF;
        }
        .input {
            background-color: #00a69c; 
        }
        .navbar {
            background-color: #00a69c;
            color: #f3a834;
            padding: 15px 30px;
            text-align: center;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar h1 {
            margin: 0;
            font-size: 50px;
            font-weight: 700;
            font-family: 'New Amsterdam', sans-serif;
        }
        .button-container {
            display: flex;
            gap: 50px;
        }
        .navbar-button {
            background-color: #f3a834;
            color: #FFFFFF;
            border: none;
            padding: 15px 25px;
            font-size: 18px;
            cursor: pointer;
            border-radius: 5px;
            text-transform: uppercase;
            font-weight: 700;
            font-family: 'Bebas Neue', sans-serif;
        }
        .navbar-button:hover {
            background-color: #d68e2b;
        }
        .content {
            margin-top: 80px;
            padding: 20px;
        }
        .welcome-message {
            font-size: 24px;
            font-weight: bold;
            color: #00a69c;
            text-align: center;
            margin: 20px 0;
        }
        .hidden {
            display: none;
        }
    </style>
    <div class="navbar">
        <h1>AstroForge HITL</h1>
        <div class="button-container">
            <button class="navbar-button" onclick="window.location.href='http://192.168.80.85:8081'">Thermocouples</button>
            <button class="navbar-button" onclick="window.location.href='http://192.168.80.85:8082'">RTDs</button>
            <button class="navbar-button" onclick="window.location.href='http://192.168.80.85:8083'">Eloads</button>
            <button class="navbar-button" onclick="window.location.href='http://192.168.80.85:8084'">INA</button>
        </div>
    </div>
    <div class="content">
        <div class="welcome-message">Welcome to the AstroForge GUI Demo!</div>
        <div class="welcome-message">Click a Button to run a script</div>
    </div>
    ''')

if __name__ == '__main__':
    start_server(show_dashboard, host='0.0.0.0', port=8080)


