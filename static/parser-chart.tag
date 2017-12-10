<parser-chart>
    <div class="container">
        <div class="row">
            <div id="donut{this.UID}" class="col" style="height: 160px; width: 100%;"></div>
        </div>
    </div>

    <script>
        var self = this;
        self.mixin(SharedMixin);
        self.total = 0;
        self.columns = [];
        
        self.transform = function(data) {
            self.total = data.total;
            var others = 0;
            Object.keys(data.status).forEach(function(key) {
                if(['pt', 'en'].indexOf(key) == -1) {
                    others += data.status[key];
                }
                else
                    self.columns.unshift([key, data.status[key]]);
            });
            self.columns.unshift(['other', others]);
            self.update();
            var chart = c3.generate({
                bindto: '#donut' + self.UID,
                data: {
                    columns: self.columns,
                    type : 'donut'
                },
                legend: {
                   position: 'right'
                },
                tooltip: {
                    format: {
                        value: function (value) { return value; }
                    }
                },
                donut: {
                    title: self.total + " entries",
                    label: {
                        show: false,
                        format: function (value) { return value; }
                    }
                }
            });
        }

        self.on('mount', function() {
            $.getJSON('/stats/parser', self.transform);

            this.source.addEventListener("parser_stats", function (e) {
                self.transform(JSON.parse(e.data))
            }, false);
        })
    </script>
</parser-chart>