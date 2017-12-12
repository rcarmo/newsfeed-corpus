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
        self.columms = [["pt",0]["en",0]["others",1]];

        self.renderTotal = function() {
            var total=0,
                data=self.chart.data.shown();
            for(var i=0,l=data.length;i<l;i++) {
                total+=data[i].values[0].value; 
            }
            d3.select('#donut'+self.UID+' .c3-chart-arcs-title').node().innerHTML = self.total;
        }

        self.transform = function(data) {
            self.total = self.activetotal = data.count;
            self.columns = [];
            var others = 0;
            Object.keys(data.lang).forEach(function(key) {
                if(['pt', 'en'].indexOf(key) == -1) {
                    others += data.lang[key];
                }
                else
                    self.columns.unshift([key, data.lang[key]]);
            });
            self.columns.unshift(['other', others]);
            self.chart.load({columns: self.columns})
            self.renderTotal();
            self.update();
        }

        self.on('mount', function() {
            self.chart = c3.generate({
                bindto: '#donut' + self.UID,
                data: {
                    columns: self.columms,
                    type : 'donut'
                },
                legend: {
                   position: 'right',
                   item: {
                       onclick: function (d) { 
                           self.chart.toggle(d);
                           self.renderTotal();
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
            $.getJSON('/stats/entries', self.transform);

            this.source.addEventListener("metrics_entries", function (e) {
                self.transform(JSON.parse(e.data).data)
            }, false);
        })
    </script>
</parser-chart>
