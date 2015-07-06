var React = require('react');
var _ = require('underscore');

var BenchmarkTable = require('./BenchmarkTable.react');
var BenchmarkStore = require('../stores/BenchmarkStore');

var BenchmarkDashboard = React.createClass({

  propTypes: {
    actions: React.PropTypes.arrayOf(React.PropTypes.object).isRequired,
  },

  render: function() {
    return (
      <div>
        <div className="container">
          <div className="row">
            <div className="col-md-12">
              <BenchmarkTable
                data={this.props.actions}
                environmentCount={BenchmarkStore.getEnvironmentCount()}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

});

module.exports = BenchmarkDashboard;
