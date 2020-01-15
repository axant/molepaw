;var AXW;
(function(AXW) {
    AXW.Requests = {
        GET: function(url) {
            return $.ajax({
                url: url,
                type: 'GET'
            });
        },
        PUT: function(url, data) {
            return $.ajax({
                url: url,
                contentType: 'application/json',
                data: JSON.stringify(data),
                type: 'PUT'
            });
        },
        POST: function(url, data) {
            return $.ajax({
                url: url,
                contentType: 'application/json',
                data: JSON.stringify(data),
                type: 'POST'
            });
        },
        DELETE: function(url) {
            return $.ajax({
                url: url,
                type: 'DELETE'
            });
        }
    };
})(AXW || (AXW = {}));
