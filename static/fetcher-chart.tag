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
        self.columns = [];
        self.colors = {
            "Pending": "#9e9e9e",
            "Unreachable": "#d50000",
            "Fetched": "#4caf50",
            "Redirected": "#81c784",
            "Inacessible": "#ff9800",
            "Error": "#ff6d00"
        }

        function label(value) {
            if(value==='None') return "Pending";
            if(value==0) return "Unreachable";
            if(value < 300) return "Fetched";
            if(value < 400) return "Redirected";
            if(value < 500) return "Inacessible";
            return "Error";
        }

        self.transform = function(data) {
            self.total = data.total;
            Object.keys(data.status).forEach(function(key) {
                self.columns.unshift([label(key), data.status[key]]);
            });
            self.update();
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
        }

        self.on('mount', function() {
            $.getJSON('/stats/fetcher', self.transform);
            // first grab a snapshot through

            this.source.addEventListener("fetcher_stats", function (e) {
                self.transform(JSON.parse(e.data))
            }, false);
        })
    </script>
</fetcher-chart>
