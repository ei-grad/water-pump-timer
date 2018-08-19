<html><head>
<style>
body {{max-width:480px;}}
h1, h3, div {{margin:1%;}}
form {{margin:0;}}
label, input {{display:inline-block;width:48%;margin:1%;}}
input[type=submit] {{width:98%;}}
input[type=text] {{text-align:right;}}
</style>
<body>
<div>{message}</div>
<h1>Water pump timer</h1>
<div>{status}</div>
<form action=switch method=POST><input type=submit value=Switch></form>
<form action=reset method=POST><input type=submit value=Reboot></form>
<form action=start method=POST><input type=submit value=Start></form>
<form action=stop method=POST><input type=submit value=Stop></form>
<h3>Configuration</h3>
<form action=config method=POST>
<label>Interval:</label><input type=text name=interval value={interval}><br/>
<label>Duration:</label><input type=text name=duration value={duration}><br/>
<label>Rounds:</label><input type=text name=rounds value={rounds}><br/>
<input type=submit value="Apply and save">
</form>
