<%inherit file="body.mako"/>

<%namespace name="helpers" file="helpers.mako"/>

<%block name="title">
  Benchmark Dashboard
</%block>

      <h1>Benchmark Results</h1>
      <div class="row">
        <div class="col-sm-12">
          <ul class="list-group results">
            <li class="list-group-item template">
              <div class="row details">
                <div class="col-sm-5 name"></div>
                <div class="col-sm-2 align-center status"></div>
                <div class="col-sm-2 align-center score"></div>
                <div class="col-sm-3 align-right time"></div>
              </div>
              <div class="list-group-item-text">
                <hr class="clear">
                <div class="row">
                  <div class="col-sm-12">
                    <pre class="command"></pre>
                  </div>
                </div>
                <div class="row">
                  <div class="col-sm-6">
                    <pre class="result"></pre></div>
                  <div class="col-sm-6">
                    <pre class="bundle"></pre></div>
                </div>
                <div class="row">
                  <div class="col-sm-4 col-sm-offset-8 align-right">
                    <a>Download</a>
                    <button type="button" class="btn btn-success">Share!</button>
                  </div>
                </div>
              </p>
            </li>
          </ul>
        </div><!-- /.col-sm-4 -->

<%def name="format_result(val)">
  %if isinstance(val, dict) and 'value' in val and 'units' in val:
    <div class="ui micro horizontal statistic">
      <div class="value">${val['value']}</div>
      <div class="label">${val['units']}</div>
    </div>
  %else:
    ${val}
  %endif
</%def>
