function numeric(v){return typeof v==='number'&&isFinite(v)&&v>=0;}
function scan(){
 var s=w.ALICE_SNAPSHOT,c=w.ALICE_CLIENT_SNAPSHOT,now=Date.now();
 var fresh=s&&now-Date.parse(s.time)>=0&&now-Date.parse(s.time)<=180000;
 var cf=c&&c.available&&now-Date.parse(c.time)>=0&&now-Date.parse(c.time)<=180000;
 text('alice-p50-cpu',fresh&&numeric(s.cpu)?s.cpu+'%':'—');
 text('alice-p50-memory',fresh&&numeric(s.memory)?s.memory+'%':'—');
 var rows=cf&&Array.isArray(c.clients)?c.clients:[],tx=0,rx=0,sessions=0,known=true,capped=false;
 rows.forEach(function(row){if(numeric(row.tx_kbps))tx+=row.tx_kbps;if(numeric(row.rx_kbps))rx+=row.rx_kbps;known=known&&numeric(row.sessions);if(numeric(row.sessions))sessions+=row.sessions;capped=capped||row.tx_capped||row.rx_capped;});
 text('alice-p50-clients',cf?rows.length:'—');text('alice-p50-up',cf?(capped?'≥':'')+tx.toFixed(1):'—');text('alice-p50-down',cf?(capped?'≥':'')+rx.toFixed(1):'—');text('alice-p50-sessions',cf&&known?sessions:'—');
 var stamp=fresh?s.time:cf?c.time:null;
 text('alice-p50-stamp',stamp?'Dữ liệu đọc lúc '+new Date(stamp).toLocaleTimeString('vi-VN'):'Chưa có số liệu mới trong 180 giây');
 text('alice-p50-source',stamp?'Nguồn: DrayOS trong phiên quản trị. Tổng lưu lượng chỉ tính các dòng Data Flow đọc được, không phải tốc độ gói cước WAN.':'Đăng nhập DrayOS và làm mới số liệu; cần bật Data Flow Monitor để có lưu lượng từng thiết bị.');
}
