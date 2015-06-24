<%def name="table_status(action_status)">
  <%
    status_map = {
      'completed': '',
      'cancelled': 'disabled',
      'failed': 'error',
      'pending': 'warning',
      'running': 'warning',
    }
  %>
  ${status_map[action_status]}
</%def>

<%def name="status(action_status)">
  <%
  status_map = {
    'completed': 'green',
    'cancelled': 'red',
    'failed': 'red',
    'pending': 'yellow',
    'running': 'yellow',
  }
  %>
  ${status_map[action_status]}
</%def>

<%def name="datetime_status(action_status)">
  <%
  datetime_map = {
    'completed': 'ERR',
    'cancelled': 'UNKNOWN',
    'failed': 'UNKNOWN',
    'pending': 'RUNNING',
    'running': 'RUNNING',
  }
  %>
  ${datetime_map[action_status]}
</%def>
