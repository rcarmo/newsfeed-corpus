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
        self.activetotal = 0;
        self.columns = [];

        self.transform = function(data) {
            self.total = self.activetotal = data.total;
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
            self.chart = c3.generate({
                bindto: '#donut' + self.UID,
                data: {
                    columns: self.columns,
                    type : 'donut'
                },
                legend: {
                   position: 'right',
                   item: {
                       onclick: function (d) { 
                           self.chart.toggle(d);
                           var total=0,
                               data=self.chart.data.shown();
                           for(var i=0,l=data.length;i<l;i++) {
                               total+=data[i].values[0].value; 
                           }
                           self.activetotal = total;
                           d3.select('#donut'+self.UID+' .c3-chart-arcs-title').node().innerHTML = self.activetotal;
                       }
                   }
                },
                tooltip: {
                    format: {
                        value: function (value) { return value; }
                    }
                },
                donut: {
                    title: self.total,
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
