<html><head>
<title>Water Pump Timer</title>
<style>
body {{font-size:3vh;}}
h1, h3, div {{margin:1%;}}
form {{margin:0;}}
label, input {{display:inline-block;width:48%;margin:1%;font-size:3vh;}}
input[type=submit] {{width:98%;}}
input[type=text] {{text-align:right;}}
</style>
<body>
<div>{message}</div>
<h1>Water pump timer</h1>
<div>{status}</div>
{actions}
<h3>Configuration</h3>
<form action=config method=POST>
<label>Load duration (s):</label><input type=text name=load_duration value={load_duration}><br/>
<label>Pump duration (s):</label><input type=text name=pump_duration value={pump_duration}><br/>
<label>Rounds:</label><input type=text name=rounds value={rounds}><br/>
<label>Load ON delay (ms):</label><input type=text name=load_on_delay value={load_on_delay}><br/>
<label>Tick period (ms):</label><input type=text name=tick_period value={tick_period}><br/>
<input type=submit value="Apply and save">
</form>
