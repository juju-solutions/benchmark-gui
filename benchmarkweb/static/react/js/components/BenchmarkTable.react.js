var React = require('react');
var BS = require('react-bootstrap');
var BenchmarkRow = require('./BenchmarkRow.react');
var _ = require('underscore');

var cx = require('classnames');
var Utils = require('../utils/Utils');
var Dot = require('./Dot.react');

const SORT_DESC = -1;
const SORT_ASC = 1;
const SORT_NONE = 0;


var BenchmarkTable = React.createClass({

  getInitialState: function() {
    return {
      sortCol: 'Started',
      sortDir: SORT_DESC,
      sortFunc: (a) => a.started || ''
    }
  },

  _getSortDir: function(col) {
    if (this.state.sortCol === col) {
      return this.state.sortDir;
    }
    return SORT_NONE;
  },

  _handleSort: function(col, dir, func) {
    this.setState({
      sortCol: col,
      sortDir: dir,
      sortFunc: func
    });
  },

  _makeColumnHeader: function(name, sortFunc) {
    return (
      <ColumnHeader
        name={name}
        sortDir={this._getSortDir(name)}
        sortFunc={sortFunc}
        onSort={this._handleSort}
      />
    );
  },

  render: function() {
    var p = this.props;
    var sortedData = _.sortBy(p.data, this.state.sortFunc);

    if (this.state.sortDir === SORT_DESC) {
      sortedData = sortedData.reverse();
    }

    var benchmarkRows = sortedData
      .map(function (action) {
        return (
          <BenchmarkRow
            key={action.uuid}
            action={action}
            environmentCount={p.environmentCount}
          />
        );
    }.bind(this));

    return (
      <div>
        <table className="table">
          <thead>
            <tr>
              {this._makeColumnHeader('Benchmark', (a) => `${a.service}:${a.name}`)}
              {this._makeColumnHeader('State', (a) => a.status)}
              {this.props.environmentCount > 1 &&
               this._makeColumnHeader('Environment', (a) => a.environment ? a.environment.name: '')}
              {this._makeColumnHeader('Unit', (a) => a.unit)}
              {this._makeColumnHeader('Result', function(a) {
                if (a.output &&
                    a.output.meta &&
                    a.output.meta.composite) {
                  return a.output.meta.composite.value;
                }
                return null;
              })}
              {this._makeColumnHeader('Duration', (a) => a.duration)}
              {this._makeColumnHeader('Started', (a) => a.started)}
            </tr>
          </thead>
          {benchmarkRows}
        </table>
      </div>
    );
  }
});

var ColumnHeader = React.createClass({
  propTypes: {
    name: React.PropTypes.string,
    sortable: React.PropTypes.bool,
    sortDir: React.PropTypes.number,
    sortFunc: React.PropTypes.func,
    onSort: React.PropTypes.func
  },

  getDefaultProps: function() {
    return {
      name: null,
      sortable: true,
      sortDir: SORT_NONE,
      sortFunc: undefined
    }
  },

  _handleClick: function() {
    if (!this.props.sortable) {
      return;
    }

    var sortDir = this.props.sortDir === SORT_NONE ?
      SORT_DESC :
      -this.props.sortDir;
    this.props.onSort(this.props.name, sortDir, this.props.sortFunc);
  },

  render: function() {
    return (
      <th
        onClick={this._handleClick}
        className={cx(this.props.sortable ? 'sortable' : false)}
      >
        {this.props.name || this.props.children}
        {this.props.sortDir === SORT_DESC &&
            <BS.Glyphicon glyph='triangle-bottom' />}
        {this.props.sortDir === SORT_ASC &&
            <BS.Glyphicon glyph='triangle-top' />}
      </th>
    );
  }
});

module.exports = BenchmarkTable;
