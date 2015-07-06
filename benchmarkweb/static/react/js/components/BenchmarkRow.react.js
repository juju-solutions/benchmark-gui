var React = require('react');
var Router = require('react-router');

var cx = require('classnames');
var YAML = require('yamljs');

var Dot = require('./Dot.react');
var Utils = require('../utils/Utils');
var BenchmarkStore = require('../stores/BenchmarkStore');

var BenchmarkRow = React.createClass({

  getInitialState: function() {
    return {
      highlighted: false,
      open: false
    };
  },

  _handleMouseOver: function() {
    this.setState({highlighted: true});
  },

  _handleMouseOut: function() {
    this.setState({highlighted: false});
  },

  _handleClick: function() {
    this.setState({open: !this.state.open});
  },

  _handlePublish: function(action) {
    var url = `/api/actions/${action.uuid}/publish`;
    $.ajax({
      url: url,
      type: 'POST',
      success: function(data) {
        alert('Benchmark published!');
      },
      error: function(xhr, status, err) {
        alert("Couldn't publish benchmark: " + err);
      }
    });
    return false;
  },

  render: function() {
    var a = this.props.action;

    return (
      <tbody
        onMouseOver={this._handleMouseOver}
        onMouseOut={this._handleMouseOut}
        onClick={this._handleClick}
        className={this.state.highlighted ? 'highlighted' : ''}
      >
        <tr>
          <td>
            {a.service}:{a.name}
          </td>
          <td className="lead">
            <Dot className={cx(Utils.statusColor(a.status))}
               title={a.status} />
          </td>
          {this.props.environmentCount > 1 &&
          <td>{a.environment ? a.environment.name: ''}</td>
          }
          <td>{a.unit}</td>
          <td>
            {a.output && a.output.meta &&
              Utils.formatResult(a.output.meta.composite)
            }
          </td>
          <td>{a.duration}</td>
          <td>{Utils.timeDeltaHtml(a.started)}</td>
        </tr>
        <tr className={this.state.open ? 'open' : 'closed'}>
          <td colSpan={this.props.environmentCount > 1 ? 7 : 6}>
            <div className="col-md-5">
              <p>Benchmark output</p>
              <textarea
                className="yaml"
                defaultValue={a.output ? YAML.stringify(a.output, 4, 2) : "No output available"}
              />
            </div>
            <div className="col-md-4">
              <p>Benchmark bundle</p>
              <textarea
                className="yaml"
                defaultValue={a.bundle || "No bundle available"}
              />
            </div>
            <div className="col-md-2">
            {BenchmarkStore.getSettings().can_publish &&
             a.duration && a.bundle &&
              <button
                className="btn btn-primary"
                onClick={() => this._handlePublish(a)}
              >Publish to cloud-benchmarks.org</button>
            }
            </div>
          </td>
        </tr>
      </tbody>
    );
  }

});

module.exports = BenchmarkRow;
