<fetcher-chart>
    <div class="container">
        <div class="row">
            <div id="donut{this.UID}" class="col" style="height: 160px; width: 100%;"></div>
        </div>
    </div>

    <script>
        var self = this;
        self.mixin(SharedMixin);
        self.total = 0;
        self.columns = [["Pending", 1]];
        self.colors = {
            "Pending": "#9e9e9e",
            "Unreachable": "#d50000",
            "Fetched": "#4caf50",
            "Redirected": "#81c784",
            "Inacessible": "#ff9800",
            "Error": "#ff6d00"
        }

        self.renderTotal = function() {
            var total=0,
                data=self.chart.data.shown();
            for(var i=0,l=data.length;i<l;i++) {
                total+=data[i].values[0].value; 
            }
            d3.select('#donut'+self.UID+' .c3-chart-arcs-title').node().innerHTML = total;
        }

        self.transform = function(data) {
            self.total = data.total;
            self.columns = [];
            Object.keys(data.status).forEach(function(key) {
                var label = key.charAt(0).toUpperCase() + key.slice(1);
                self.columns.unshift([label, data.status[key]]);
            });
            console.log(self.columns)
            self.chart.load({columns: self.columns})
            self.renderTotal();
            self.update();
        }

        self.on('mount', function() {
            self.chart = c3.generate({
                bindto: '#donut' + self.UID,
                data: {
                    columns: self.columns,
                    type : 'donut',
                    colors: self.colors
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
                           d3.select('#donut'+self.UID+' .c3-chart-arcs-title').node().innerHTML = total;
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
            $.getJSON('/stats/feeds', self.transform);
            // first grab a snapshot through

            this.source.addEventListener("metrics_feeds", function (e) {
                self.transform(JSON.parse(e.data).data)
            }, false);
        })
    </script>
</fetcher-chart>
