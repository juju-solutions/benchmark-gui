var React = require('react');
var Router = require('react-router');
var _ = require('underscore');

var App = require('./components/App.react')
var BenchmarkStore = require('./stores/BenchmarkStore');
var BenchmarkDashboard = require('./components/BenchmarkDashboard.react');
var BenchmarkActions = require('./actions/BenchmarkActions');

var DefaultRoute = Router.DefaultRoute;
var Route = Router.Route;

var WEB_SOCKET_SWF_LOCATION = "/static/WebSocketMain.swf";
var WEB_SOCKET_DEBUG = true;

var BenchmarkDashboardWrapper = React.createClass({
  render: function() {
    var data = BenchmarkStore.getAll();
    return (
      <BenchmarkDashboard
        actions={_.values(BenchmarkStore.getIndex())}
      />
    );
  }
});

var routes = (
  <Route name="app" path="/" handler={App}>
    <DefaultRoute handler={BenchmarkDashboardWrapper}/>
  </Route>
);

Router.run(routes, function (Handler) {
  React.render(
    <Handler/>,
    document.getElementById('content')
  );
});
