<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">

	<title>Monitor</title>
	<meta name="description" content="Monitoring front-end">
  <!-- favicons and sundry -->
  <link rel="stylesheet" href="http://fonts.googleapis.com/css?family=Roboto:300,400,500,700" type="text/css">
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
  <link type="text/css" rel="stylesheet" href="/css/materialize.min.css"  media="screen,projection"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <!--[if IE]>
  <script src="/js/history.min.js"></script>
  <script src="/js/eventsource.min.js"></script>
  <![endif]-->
</head>
<body>
 <nav class="blue lighten-1" role="navigation">
    <div class="nav-wrapper container"><a id="logo-container" href="#" class="brand-logo">News</a>
      <ul class="right hide-on-med-and-down">
        <li><a href="#"></a></li>
      </ul>

      <ul id="nav-mobile" class="sidenav">
        <li><a href="#"></a></li>
      </ul>
      <a href="#" data-target="nav-mobile" class="sidenav-trigger"><i class="material-icons">menu</i></a>
    </div>
  </nav>
  <div class="section no-pad-bot" id="index-banner">
    <div class="container">
      <div class="row">
        <div class="col s12 m6">
          <div class="card white">
            <div class="card-content black-text">
              <span class="card-title">Feeeds</span>
              <feed-count></feed-count>
            </div>
            <div class="card-action">
              <a href="#">More...</a>
            </div>
          </div>
        </div>
        <div class="col s12 m6">
          <div class="card white">
            <div class="card-content black-text">
              <span class="card-title">Fetch Status</span>
              <fetch-table></fetch-table>
            </div>
            <div class="card-action">
              <a href="#">More...</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="container">
    <div class="section">
    </div>
  </div>

  <footer class="page-footer orange">
    <div class="container">
      <div class="row">
      </div>
    </div>
    <div class="footer-copyright">
      <div class="container">
      Made using <a class="orange-text text-lighten-3" href="http://materializecss.com">Materialize</a>
      </div>
    </div>
  </footer>

  <script defer src="/js/materialize.min.js"></script>
  <script type="riot/tag" src="fetch-table.tag"></script>
  <script src="/js/riot+compiler.min.js"></script>
  <script src="/js/route.min.js"></script>
  <script src="/js/zepto.min.js"></script>
  <script>
    var SharedMixin = {
      observable: riot.observable(),
      source: new EventSource('/events')
    };
    riot.compile(function() {
      riot.mount('*')
      route.start(true)
    })
  </script>
</body>
</html>
