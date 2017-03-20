<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">

	<title>Monitor</title>
	<meta name="description" content="Monitoring front-end">

	<link href="css/minimal.css" rel="stylesheet">
    <!--[if IE]>
    <script src="js/history.min.js"></script>
    <script src="js/eventsource.min.js"></script>
    <![endif]-->
</head>
<body>
    <div class="container">
        <header>
            <nav class="float-right">
                <ul>
                    <li>${timestr}</li>
                    <li><sse-counter></sse-counter></li>
                </ul>
            </nav>
        </header>
        <div class="row">
            <div class="col-12">
                <h1>Stateless Demo App</h1>
                <hr>
                <p>This is a small stateless webapp for demoing load balancing. While each instance maintains a request count to demonstrate load sharing among instances, the count is not preserved if the app is restarted.</p>
            </div>
        </div>
    <hr>

    <div class="row">
        <div class="col-6">
            <div class="text-center">
                <h2>Server Environment</h2>
            </div>
            <hr>
<% from os import environ %>
            <table class="table">
                <tr>
                    <th scope="col">Variable Name</th>
                    <th scope="col">Value</th>
                </tr>
% for k, v in sorted(list(environ.items())):
                <tr>
                    <th scope="row">${k}</th>
                    <td>${v}</td>
                </tr>
% endfor
            </table><!-- table -->
        </div>
        <div class="col-6">
            <div class="text-center">
                <h2>Request Environment</h2>
            </div>
            <hr>
            <table class="table">
                <tr>
                    <th scope="col">Variable Name</th>
                    <th scope="col">Value</th>
                </tr>
% for k, v in sorted(list(environ.items())):
                <tr>
                    <th scope="row">${k}</th>
                    <td>${v}</td>
                </tr>
% endfor
            </table><!-- table -->
        </div>
        </div>

        <footer>
                <a href="https://github.com/rcarmo">@rcarmo</a> <a class="float-right" href="http://minimalcss.com">Minimal CSS</a>
        </footer><!-- footer -->
    </div>
    <script type="riot/tag" src="sse-counter.tag"></script>
    <script src="js/riot+compiler.min.js"></script>
    <script src="js/route.min.js"></script>
    <script>
      riot.compile(function() {
        riot.mount('*')
        route.start(true)
      })
    </script>
</body>
</html>
