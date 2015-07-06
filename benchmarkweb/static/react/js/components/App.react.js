var React = require('react');
var Router = require('react-router');

var BenchmarkActions = require('../actions/BenchmarkActions');
var BenchmarkStore = require('../stores/BenchmarkStore');
var BenchmarkActions = require('../actions/BenchmarkActions');

var RouteHandler = Router.RouteHandler;

/**
 * Retrieve the current Benchmark data from the BenchmarkStore
 */
function getBenchmarkState() {
  return BenchmarkStore.getAll();
}

var App = React.createClass({

  getInitialState: function() {
    return {};
  },

  componentWillMount: function() {
    var socket = io.connect('/events');

    $(window).bind("beforeunload", function() {
      socket.disconnect();
    });

    socket.on("event", function(e) {
      //console.log(JSON.stringify(e));
      BenchmarkActions.refreshAll();
    });

    socket.on("user_connect", function() {
      console.log("websocket connected");
    });
  },

  componentDidMount: function() {
    BenchmarkStore.addChangeListener(this._onChange);
    BenchmarkActions.refreshAll();
  },

  componentWillUnmount: function() {
    BenchmarkStore.removeChangeListener(this._onChange);
  },

  render: function () {
    // Don't render if we don't have data yet
    if (Object.keys(this.state).length === 0) {
      return <div/>;
    }

    return (
      <div>
        <Nav environment={BenchmarkStore.getEnvironment()}/>
        <RouteHandler/>
      </div>
    );
  },

  /**
   * Event handler for 'change' events coming from the BenchmarkStore
   */
  _onChange: function() {
    this.setState(getBenchmarkState());
  }

});

var Nav = React.createClass({
  render: function() {

    return (
      <nav className="navbar">
        <div className="container">
          <p className="navbar-text pull-right">
            Environment: {this.props.environment.name}
          </p>
          <div className="navbar-header">
            <a className="navbar-brand" href="#">Benchmark GUI</a>
          </div>
        </div>
      </nav>
    );
  }
});

module.exports = App;
