/* Explicit configuration controls through the original authenticated forms.
 * Native Auto-Adjustment is controlled through the verified OEM bandwidth form.
 */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) module.exports = factory;
    else {
        var auth = document.getElementById('alice-form-auth');
        var controller = window.ALICE_CONTROLLER = factory(window, document, window.ALICE_CONTEXT ? window.ALICE_CONTEXT.host() : parent, window.ALICE_CONTEXT ? window.ALICE_CONTEXT.auth() : (new URL(window.location.href)).searchParams.get('sFormAuthStr') || (auth ? auth.value : ''));
        document.getElementById('apply-ppa').onclick = function () { controller.start('ppa', false); };
        document.getElementById('apply-auto').onclick = function () { controller.start('ppa', false, 'auto'); };
        document.getElementById('apply-shared').onclick = function () { controller.start('shared', false); };
        document.getElementById('undo-ppa').onclick = function () { controller.start('ppa', true); };
        document.getElementById('undo-shared').onclick = function () { controller.start('shared', true); };
        document.getElementById('read-config').onclick = controller.inspect;
        document.getElementById('export-report').onclick = controller.exportReport;
        document.getElementById('clear-audit').onclick = controller.clearAudit;
        ['flow', 'sessions', 'ping', 'trace', 'system'].forEach(function (name) {
            document.getElementById('diag-' + name).onclick = function () { controller.navigate(name); };
        });
    }
}(this, function (win, doc, host, auth) {
    'use strict';
    var frame = doc.getElementById('native-control');
    var status = doc.getElementById('control-status');
    var op = null, timer = null, nonce = 0;
    var configuration = win.ALICE_CONFIG_STATE || {ppa: null, bw4: null, bw6: null};
    var reads = {ppa: null, bandwidth: null};
    var historyKey = 'alice.draysos.controls.v1.audit';
    var specs = {
        ppa: {path: '../cgi-bin/ipnat.cgi', query: 'fid=20&iAct=0', fid: '20',
            values: {iHwSetFlag: '2', iTcp: true, iUdp: true, iTraffic: true, iQos: false, iSpecific: false}},
        shared: {path: '../cgi-bin/v2x00.cgi', query: 'fid=302', fid: '302',
            values: {sIpBandwEnable: '0', sIpBandwEnable_v6: '0', iSmartEnable: false}},
        elastic: {path: '../cgi-bin/v2x00.cgi', query: 'fid=302', fid: '302',
            values: {sIpBandwEnable:'1',chkBandwAuto:true,sIpBandwDefTx:'0',sIpBandwDefRx:'0',iDefTx:'0',iDefRx:'0'}}
    };
    var helpers = ['printTitle', 'printLogo', 'writeNote', 'cpntCtrl', 'getIdxbyName',
        'getIdxOfForm', 'getVleFromElmt', 'setVle2Elmt', 'hideElmtByClass',
        'showElmtByClass', 'showElmtById', 'choosePc', 'inet_addr', 'isEqualLan',
        'isIPv6', 'isStrIp', 'strFormat', 'transitIpv6'];
    var forwarded = ['SHOW_BDW_QOS', 'SHOW_LAN_GEN_2NDSUBNET', 'sIPBandwTag'];
    var diagnoses = {
        flow: {path: '../cgi-bin/v2x00.cgi?fid=2096', flag: 'SHOW_DIG_DATAM'},
        sessions: {path: '../cgi-bin/ipnatpm.cgi?', flag: 'SHOW_SYS_ADMIN'},
        ping: {path: '../cgi-bin/v2x00.cgi?fid=2095', flag: 'SHOW_DIG_IPPING'},
        trace: {path: '../cgi-bin/v2x00.cgi?fid=2097', flag: 'SHOW_DIG_IPTRACERT'},
        system: {path: '../cgi-bin/v2x00.cgi?fid=2015', flag: 'SHOW_SYS_ADMIN'}
    };
    function journal() {
        try {
            var list = JSON.parse(win.sessionStorage.getItem(historyKey) || '[]');
            return Array.isArray(list) ? list.slice(-100) : [];
        } catch (ignored) { return []; }
    }
    function showJournal() {
        var list = doc.getElementById('audit-list');
        if (!list) return;
        while (list.firstChild) list.removeChild(list.firstChild);
        journal().slice(-12).reverse().forEach(function (entry) {
            var item = doc.createElement('li'); item.textContent = entry.time + ' | ' + entry.action + ' | ' + entry.result; list.appendChild(item);
        });
    }
    function log(action, result) {
        try {
            var list = journal(); list.push({time: new Date().toISOString(), action: action, result: result});
            win.sessionStorage.setItem(historyKey, JSON.stringify(list.slice(-100))); showJournal();
        } catch (ignored) {}
    }
    function updateConfiguration(view, kind) {
        if (kind === 'ppa') { configuration.ppa = Number(view.iPpaFlag); reads.ppa = new Date().toISOString(); }
        else { configuration.bw4 = Number(view.sIpBandwFlag); configuration.bw6 = Number(view.sIpBandwFlag_v6); configuration.smart = Number(view.iIpSmartBWFlag); configuration.auto_adjust=(configuration.bw4>>>11)&1;configuration.limit_tx_kbps=decodeRate(Number(view.sIpBandwDefTx));configuration.limit_rx_kbps=decodeRate(Number(view.sIpBandwDefRx));reads.bandwidth = new Date().toISOString(); }
        if (typeof win.ALICE_UPDATE_CONFIG === 'function') win.ALICE_UPDATE_CONFIG(configuration);
    }
    function decodeRate(raw){return raw===65534||!Number.isInteger(raw)||raw<0||raw>65535?null:(raw&32767)*((raw&32768)?1000:1);}
    function encodeRate(kbps){if(!Number.isInteger(kbps)||kbps<1||kbps>30000000)throw new Error('Ngưỡng băng thông phải từ 1 Kbps đến 30000 Mbps.');if(kbps<=30000)return{value:String(kbps),unit:'0'};if(kbps%1000!==0)throw new Error('Ngưỡng trên 30 Mbps cần là số Mbps nguyên theo form modem.');return{value:String(kbps/1000),unit:'1'};}
    function elasticValues(profile){if(!profile||typeof profile!=='object')throw new Error('Nhập ngưỡng upload/download mỗi thiết bị trước khi bật chia sẻ linh hoạt.');var tx=encodeRate(profile.tx_kbps),rx=encodeRate(profile.rx_kbps);return{sIpBandwEnable:'1',chkBandwAuto:true,sIpBandwDefTx:tx.value,sIpBandwDefRx:rx.value,iDefTx:tx.unit,iDefRx:rx.unit};}
    function message(value) { status.textContent = value; if (typeof win.ALICE_CONTROL_NOTICE === 'function') win.ALICE_CONTROL_NOTICE(value); }
    function admin() { var v = host && host.SHOW_SYS_ADMIN; return v === true || (Number.isFinite(Number(v)) && (Number(v) & 2097152) === 2097152); }
    function validAuth(value) { return typeof value === 'string' && value.length > 0 && !/[<>"'\r\n]/.test(value); }
    function bridge() {
        helpers.forEach(function (name) {
            if (typeof host[name] === 'function') win[name] = function () { return host[name].apply(host, arguments); };
        });
        forwarded.forEach(function (name) {
            try { Object.defineProperty(win, name, {configurable: true, get: function () { return host[name]; },
                set: function (value) { host[name] = value; }}); } catch (ignored) {}
        });
    }
    function field(form, name) {
        var el = form.elements && (form.elements.namedItem ? form.elements.namedItem(name) : form.elements[name]);
        return el || form[name];
    }
    function value(form, name) {
        var el = field(form, name);
        if (!el) throw new Error('Thi\u1ebfu tr\u01b0\u1eddng c\u1ea5u h\u00ecnh: ' + name);
        if (typeof el.length === 'number' && !el.tagName && !el.type) {
            for (var i = 0; i < el.length; i++) if (el[i].checked) return String(el[i].value);
            throw new Error('Ch\u01b0a c\u00f3 l\u1ef1a ch\u1ecdn: ' + name);
        }
        return el.type === 'checkbox' || el.type === 'radio' ? !!el.checked : String(el.value);
    }
    function read(form, kind) {
        var out = {};
        Object.keys(specs[kind].values).forEach(function (name) { out[name] = value(form, name); });
        if (kind === 'ppa' && !/^[012]$/.test(out.iHwSetFlag)) throw new Error('Ch\u1ebf \u0111\u1ed9 PPA kh\u00f4ng h\u1ee3p l\u1ec7.');
        if (kind === 'shared' && (!/^[01]$/.test(out.sIpBandwEnable) || !/^[01]$/.test(out.sIpBandwEnable_v6)))
            throw new Error('C\u1edd gi\u1edbi h\u1ea1n b\u0103ng th\u00f4ng kh\u00f4ng h\u1ee3p l\u1ec7.');
        return out;
    }
    function matchesActual(view, kind, target) {
        if(kind==='elastic')return String(Number(view.sIpBandwFlag)&1)===target.sIpBandwEnable&&!!(Number(view.sIpBandwFlag)&2048)===target.chkBandwAuto&&Number(view.sIpBandwDefTx)===Number(target.sIpBandwDefTx)+(target.iDefTx==='1'?32768:0)&&Number(view.sIpBandwDefRx)===Number(target.sIpBandwDefRx)+(target.iDefRx==='1'?32768:0);
        if (kind === 'shared') return String(Number(view.sIpBandwFlag) & 1) === target.sIpBandwEnable &&
            String(Number(view.sIpBandwFlag_v6) & 1) === target.sIpBandwEnable_v6 && !!(Number(view.iIpSmartBWFlag) & 1) === target.iSmartEnable;
        var flag = Number(view.iPpaFlag), mode = Number(target.iHwSetFlag);
        if ((flag & 3) !== mode) return false;
        if (!mode) return true; // disabled-mode UI defaults are not protocol measurements
        return !!(flag & 32) === target.iTcp && !!(flag & 64) === target.iUdp &&
            (mode === 2 ? !(flag & 24) : !!(flag & 4)) === target.iTraffic && !!(flag & 8) === target.iQos && !!(flag & 16) === target.iSpecific;
    }
    function equal(a, b) {
        return Object.keys(a).length === Object.keys(b).length && Object.keys(a).every(function (name) { return a[name] === b[name]; });
    }
    function set(form, values) {
        Object.keys(values).forEach(function (name) {
            var el = field(form, name), val = values[name];
            if (!el) throw new Error('Thi\u1ebfu tr\u01b0\u1eddng c\u1ea5u h\u00ecnh: ' + name);
            if (typeof el.length === 'number' && !el.tagName && !el.type) {
                var found = false;
                for (var i = 0; i < el.length; i++) { el[i].checked = String(el[i].value) === val; if (el[i].checked) found = true; }
                if (!found) throw new Error('L\u1ef1a ch\u1ecdn kh\u00f4ng h\u1ee3p l\u1ec7: ' + name);
            } else if (el.type === 'checkbox' || el.type === 'radio') el.checked = val;
            else el.value = val;
        });
    }
    function key(kind) { return 'alice.draysos.controls.v1.' + kind; }
    function validSettings(settings, kind) {
        if (!settings || typeof settings !== 'object' || Object.keys(settings).length !== Object.keys(specs[kind].values).length) return false;
        return Object.keys(settings).every(function (name) {
            if (!Object.prototype.hasOwnProperty.call(specs[kind].values, name)) return false;
            if (name === 'iHwSetFlag') return typeof settings[name] === 'string' && /^[012]$/.test(settings[name]);
            if (kind === 'shared' && name !== 'iSmartEnable') return typeof settings[name] === 'string' && /^[01]$/.test(settings[name]);
            if(kind==='elastic'){if(name==='chkBandwAuto')return typeof settings[name]==='boolean';if(name==='sIpBandwEnable'||name==='iDefTx'||name==='iDefRx')return typeof settings[name]==='string'&&/^[01]$/.test(settings[name]);return typeof settings[name]==='string'&&/^\d+$/.test(settings[name])&&Number(settings[name])<=30000;}
            return typeof settings[name] === 'boolean';
        });
    }
    function store(kind, record) { win.sessionStorage.setItem(key(kind), JSON.stringify(record)); }
    function saved(kind) {
        var text = win.sessionStorage.getItem(key(kind));
        if (!text) return null;
        var record = JSON.parse(text);
        if (record.kind !== kind || !validSettings(record.before, kind) || !validSettings(record.applied, kind) ||
            !isFinite(record.timestamp) || typeof record.timestamp !== 'number' || record.timestamp > Date.now() + 60000 || Date.now() - record.timestamp > 3600000)
            throw new Error('B\u1ea3n kh\u00f4i ph\u1ee5c kh\u00f4ng h\u1ee3p l\u1ec7 ho\u1eb7c \u0111\u00e3 qu\u00e1 m\u1ed9t gi\u1edd.');
        return record;
    }
    function route(kind) {
        return specs[kind].path + '?' + specs[kind].query + '&sFormAuthStr=' + encodeURIComponent(auth) + '&aliceReload=' + (++nonce);
    }
    function armTimeout() {
        if (timer !== null) win.clearTimeout(timer);
        timer = win.setTimeout(function () {
            if (op) finish('Ch\u01b0a nh\u1eadn \u0111\u01b0\u1ee3c x\u00e1c nh\u1eadn t\u1eeb DrayOS. Kh\u00f4ng k\u1ebft lu\u1eadn \u0111\u00e3 \u00e1p d\u1ee5ng; b\u1ea3n kh\u00f4i ph\u1ee5c v\u1eabn \u0111\u01b0\u1ee3c gi\u1eef.');
        }, 20000);
    }
    function finish(text, success) {
        var completed = op;
        if (op) log((op.readOnly ? 'read:' : (op.undo ? 'restore:' : 'apply:')) + op.kind, text);
        if (timer !== null) win.clearTimeout(timer);
        timer = null; op = null; frame.style.pointerEvents = ''; message(text);
        if (completed && completed.done) completed.done({ok: !!success, kind: completed.kind, message: text, configuration: Object.assign({}, configuration), read_times: Object.assign({}, reads)});
    }
    function ready() {
        var view = frame.contentWindow, form = view && view.document && view.document.forms && view.document.forms.frm1;
        if (!form || view.f !== form || typeof view.onClkBtnOk !== 'function') throw new Error('Form DrayOS ch\u01b0a s\u1eb5n s\u00e0ng.');
        if (!Array.isArray(view.inputsData) || view.inputsData.length !== view.document.getElementsByTagName('input').length || !Array.isArray(view.selectsData) || view.selectsData.length !== view.document.getElementsByTagName('select').length) throw new Error('Form DrayOS chưa khởi tạo đầy đủ.');
        var target = new win.URL(form.action, view.location.href);
        var expected = new win.URL(specs[op.kind].path, win.location.href);
        if (target.origin !== expected.origin || target.pathname.toLowerCase() !== expected.pathname.toLowerCase() ||
            String(form.method).toLowerCase() !== 'post' || String(field(form, 'fid').value) !== specs[op.kind].fid)
            throw new Error('Form kh\u00f4ng kh\u1edbp \u0111\u01b0\u1eddng c\u1ea5u h\u00ecnh g\u1ed1c.');
        var token = field(form, 'sFormAuthStr');
        if (!token || !validAuth(token.value) || token.value !== auth) throw new Error('Phi\u00ean qu\u1ea3n tr\u1ecb \u0111\u00e3 thay \u0111\u1ed5i; m\u1edf l\u1ea1i trang AI.');
        var flags = op.kind === 'ppa' ? [view.iPpaFlag] : [view.sIpBandwFlag, view.sIpBandwFlag_v6, view.iIpSmartBWFlag];
        flags.forEach(function (flag) {
            var n = Number(flag), min = op.kind === 'ppa' ? 0 : -2147483648, max = op.kind === 'ppa' ? 65535 : 4294967295;
            if (!/^-?\d+$/.test(String(flag)) || !isFinite(n) || n < min || n > max) throw new Error('Ch\u01b0a \u0111\u1ecdc \u0111\u01b0\u1ee3c tr\u1ea1ng th\u00e1i t\u1eeb DrayOS.');
        });
        if (op.kind !== 'ppa' && (!Array.isArray(view.aryIpBandw) || !Array.isArray(view.aryIpBandw_v6)))
            throw new Error('Ch\u01b0a t\u1ea3i \u0111\u1ee7 danh s\u00e1ch gi\u1edbi h\u1ea1n; d\u1eebng \u0111\u1ec3 b\u1ea3o to\u00e0n c\u1ea5u h\u00ecnh.');
        if (op.kind !== 'ppa') {
            var capacity = Number(view.ibwLmt);
            if (!Number.isInteger(capacity) || capacity < 1 || capacity > 1024 || view.aryIpBandw.length > capacity || view.aryIpBandw_v6.length > capacity) throw new Error('Dung lượng danh sách giới hạn chưa hợp lệ.');
            for (var row = 0; row < capacity; row++) if (!field(form, 'sIpBandwidth' + row) || !field(form, 'sIp6Bandwidth' + row)) throw new Error('Form thiếu trường giữ danh sách giới hạn.');
        }
        return {view: view, form: form};
    }
    function loaded() {
        if (!op) return;
        try {
            if (!admin()) throw new Error('C\u1ea7n phi\u00ean qu\u1ea3n tr\u1ecb admin.');
            if (op.phase === 'post') { op.phase = 'verify'; armTimeout(); frame.src = route(op.kind); return; }
            var current = ready(), state = read(current.form, op.kind);
            if (op.readOnly) {
                updateConfiguration(current.view, op.kind);
                if (op.kind === 'ppa') { op.kind = 'shared'; frame.src = route('shared'); armTimeout(); return; }
                finish('Đã đọc lại cấu hình PPA và giới hạn băng thông từ DrayOS. Không gửi thay đổi.', true); return;
            }
            if (op.phase === 'verify') {
                if (!equal(state, op.target) || !matchesActual(current.view, op.kind, op.target)) throw new Error('DrayOS ch\u01b0a x\u00e1c nh\u1eadn c\u00e1c thi\u1ebft l\u1eadp y\u00eau c\u1ea7u. B\u1ea3n kh\u00f4i ph\u1ee5c v\u1eabn \u0111\u01b0\u1ee3c gi\u1eef.');
                updateConfiguration(current.view, op.kind);
                if (op.undo) win.sessionStorage.removeItem(key(op.kind));
                finish(op.undo ? '\u0110\u00e3 \u0111\u1ecdc l\u1ea1i t\u1eeb DrayOS v\u00e0 x\u00e1c nh\u1eadn kh\u00f4i ph\u1ee5c c\u00e1c thi\u1ebft l\u1eadp.' :
                    '\u0110\u00e3 \u0111\u1ecdc l\u1ea1i t\u1eeb DrayOS v\u00e0 x\u00e1c nh\u1eadn c\u00e1c thi\u1ebft l\u1eadp. \u0110i\u1ec1u n\u00e0y ch\u01b0a ch\u1ee9ng minh t\u1ed1c \u0111\u1ed9 ho\u1eb7c c\u00e2n b\u1eb1ng t\u1ea3i.', true);
                return;
            }
            var before, target;
            if (op.undo) {
                var record = saved(op.kind);
                if (!record) throw new Error('Kh\u00f4ng c\u00f3 b\u1ea3n kh\u00f4i ph\u1ee5c trong phi\u00ean n\u00e0y.');
                if (equal(state, record.before) && matchesActual(current.view, op.kind, record.before)) { win.sessionStorage.removeItem(key(op.kind)); updateConfiguration(current.view, op.kind); finish('Đã xác nhận cấu hình đang ở trạng thái trước thao tác. Không ghi lại.', true); return; }
                if (!equal(state, record.applied)) throw new Error('Thi\u1ebft l\u1eadp \u0111\u00e3 \u0111\u1ed5i \u1edf n\u01a1i kh\u00e1c. D\u1eebng kh\u00f4i ph\u1ee5c \u0111\u1ec3 kh\u00f4ng ghi \u0111\u00e8.');
                before = state; target = record.before;
            } else {
                target = op.requested || Object.assign({},state,{chkBandwAuto:false});
                if (equal(state, target) && matchesActual(current.view, op.kind, target)) { updateConfiguration(current.view, op.kind); finish('C\u00e1c thi\u1ebft l\u1eadp y\u00eau c\u1ea7u \u0111\u00e3 c\u00f3 s\u1eb5n. Kh\u00f4ng g\u1eedi thay \u0111\u1ed5i.', true); return; }
                var previous = null; try { previous = saved(op.kind); } catch (expired) { win.sessionStorage.removeItem(key(op.kind)); }
                if (previous && !equal(state, previous.applied) && !equal(state, previous.before)) throw new Error('C\u1ea5u h\u00ecnh \u0111\u00e3 \u0111\u1ed5i sau l\u1ea7n \u00e1p d\u1ee5ng tr\u01b0\u1edbc. D\u00f9ng form g\u1ed1c \u0111\u1ec3 x\u1eed l\u00fd b\u1ea3n kh\u00f4i ph\u1ee5c c\u0169.');
                before = previous ? previous.before : state;
                /* Store only controlled settings; no session credential is saved. */
                op.previousRecord = previous; op.createdRecord = true; store(op.kind, {kind: op.kind, timestamp: Date.now(), before: before, applied: target});
            }
            set(current.form, target);
            if (op.kind !== 'ppa' && typeof current.view.oncheck === 'function') current.view.oncheck();
            if (op.kind === 'ppa') {
                if (typeof current.view.onChangeType !== 'function') throw new Error('Thi\u1ebfu x\u1eed l\u00fd ch\u1ebf \u0111\u1ed9 PPA g\u1ed1c.');
                current.view.onChangeType(); set(current.form, target);
            }
            op.target = target;
            var submitted = false, submit = current.form.submit;
            if (typeof submit !== 'function') throw new Error('Form kh\u00f4ng th\u1ec3 g\u1eedi y\u00eau c\u1ea7u.');
            current.form.submit = function () {
                submitted = true; current.form.submit = submit; op.phase = 'post'; armTimeout();
                message('\u0110\u00e3 g\u1eedi y\u00eau c\u1ea7u b\u1eb1ng form DrayOS; \u0111ang ch\u1edd \u0111\u1ecdc l\u1ea1i tr\u1ea1ng th\u00e1i.');
                return submit.call(current.form);
            };
            try { current.view.onClkBtnOk(); } finally { current.form.submit = submit; }
            if (!submitted) {
                set(current.form, state);
                if (op.kind === 'ppa') { current.view.onChangeType(); set(current.form, state); }
                if (!op.undo) { if (op.previousRecord) store(op.kind, op.previousRecord); else win.sessionStorage.removeItem(key(op.kind)); }
                finish('Form DrayOS \u0111\u00e3 ch\u1eb7n y\u00eau c\u1ea7u. Ki\u1ec3m tra th\u00f4ng b\u00e1o v\u00e0 xung \u0111\u1ed9t WAN Budget trong form b\u00ean d\u01b0\u1edbi.');
            }
        } catch (err) {
            if (op && op.phase === 'load' && !submitted && current && state) {
                try { set(current.form, state); if (op.createdRecord) { if (op.previousRecord) store(op.kind, op.previousRecord); else win.sessionStorage.removeItem(key(op.kind)); } } catch (ignored) {}
            }
            finish(err.message);
        }
    }
    function start(kind, undo, profile, readOnly) {
        if (win.ALICE_CONTEXT) auth = win.ALICE_CONTEXT.auth() || auth;
        if (op) { message('\u0110ang x\u1eed l\u00fd m\u1ed9t y\u00eau c\u1ea7u. Ch\u1edd x\u00e1c nh\u1eadn tr\u01b0\u1edbc khi thao t\u00e1c ti\u1ebfp.'); return false; }
        if (!Object.prototype.hasOwnProperty.call(specs, kind)) return false;
        if (!admin() || !validAuth(auth)) { message('C\u1ea7n phi\u00ean qu\u1ea3n tr\u1ecb h\u1ee3p l\u1ec7. M\u1edf AI t\u1eeb menu admin.'); return false; }
        if (typeof host.setVle2Elmt !== 'function' || typeof host.getVleFromElmt !== 'function') {
            message('Ch\u01b0a c\u00f3 m\u00f4i tr\u01b0\u1eddng form DrayOS. M\u1edf AI t\u1eeb menu c\u1ee7a router.'); return false;
        }
        try {
            if(kind==='shared'&&!undo&&!readOnly&&!win.confirm('Lệnh này tắt giới hạn IPv4, IPv6 và Smart Limit; không phải cân bằng QoS. Bạn muốn bỏ các giới hạn này?'))throw new Error('Đã hủy bỏ giới hạn; không gửi thay đổi.');
            if(profile&&kind!=='elastic'&&(kind!=='ppa'||profile!=='auto'))throw new Error('Hồ sơ không hợp lệ.');
            if(!undo&&!readOnly&&(kind==='shared'||kind==='elastic')){var other=kind==='shared'?'elastic':'shared';if(saved(other))throw new Error('Khôi phục chế độ băng thông trước đó trước khi chuyển chế độ.');}
            if (undo && !saved(kind)) throw new Error('Kh\u00f4ng c\u00f3 b\u1ea3n kh\u00f4i ph\u1ee5c trong phi\u00ean n\u00e0y.');
            if (!readOnly) { var probe = key('probe'); win.sessionStorage.setItem(probe, '1'); win.sessionStorage.removeItem(probe); }
            var target = specs[kind].values;
            if(kind==='elastic'&&!undo)target=profile&&profile.enabled===false?null:elasticValues(profile);
            if (profile === 'auto') target = {iHwSetFlag: '1', iTcp: true, iUdp: true, iTraffic: true, iQos: false, iSpecific: false};
            bridge(); op = {kind: kind, undo: !!undo, phase: 'load', readOnly: !!readOnly, requested: target};
            frame.style.display = 'block'; frame.style.pointerEvents = 'none'; frame.src = route(kind);
            message('\u0110ang t\u1ea3i to\u00e0n b\u1ed9 form c\u1ea5u h\u00ecnh hi\u1ec7n t\u1ea1i. Ch\u01b0a g\u1eedi thay \u0111\u1ed5i.'); armTimeout(); return true;
        } catch (err) { finish(err.message); return false; }
    }
    function execute(kind, undo, profile, readOnly) {
        if (op) return Promise.resolve({ok:false, message:'Đang có thao tác khác. Chờ đọc lại hoàn tất.'});
        return new Promise(function (resolve) {
            if (!start(kind === 'read' ? 'ppa' : kind, !!undo, profile || null, !!readOnly)) { resolve({ok:false, message:status.textContent}); return; }
            if (op) op.done = resolve; else resolve({ok:false, message:status.textContent});
        });
    }
    function navigate(name) {
        var entry = diagnoses[name];
        if (op || !entry || !admin() || !validAuth(auth)) return false;
        if (!host[entry.flag]) { message('C\u00f4ng c\u1ee5 n\u00e0y ch\u01b0a \u0111\u01b0\u1ee3c b\u1eadt cho model ho\u1eb7c phi\u00ean hi\u1ec7n t\u1ea1i.'); return false; }
        var target = entry.path + (entry.path.charAt(entry.path.length - 1) === '?' ? '' : '&') + 'sFormAuthStr=' + encodeURIComponent(auth);
        log('diagnostic:' + name, 'M\u1edf c\u00f4ng c\u1ee5 g\u1ed1c c\u1ee7a DrayOS');
        if (host.main) host.main.location = target; else win.location.href = target;
        return true;
    }
    function exportReport() {
        if (!admin()) { message('C\u1ea7n phi\u00ean admin \u0111\u1ec3 xu\u1ea5t b\u00e1o c\u00e1o.'); return false; }
        var backups = {};
        ['ppa', 'shared', 'elastic'].forEach(function (kind) { try { backups[kind] = saved(kind); } catch (ignored) { backups[kind] = null; } });
        var report = {schema: 'alice-router-report-v1', generated: new Date().toISOString(),
            build_target: 'Vigor2133n / 3.9.7_Anphat / P24-GHQ-HALO-WINE-ELASTIC', configuration: configuration,
            confirmed_read_times: reads, controlled_setting_backups: backups, events: journal(),
            native_heartbeat_verified: false, adaptive_mesh_controller: false,
            note: 'B\u00e1o c\u00e1o c\u1edd c\u1ea5u h\u00ecnh; kh\u00f4ng ph\u1ea3i b\u1ea3n sao to\u00e0n b\u1ed9 NVRAM ho\u1eb7c b\u1eb1ng ch\u1ee9ng throughput.'};
        var blob = new win.Blob([JSON.stringify(report, null, 2)], {type: 'application/json'});
        var url = win.URL.createObjectURL(blob), link = doc.createElement('a');
        link.href = url; link.download = 'Alice_router_report.json'; doc.body.appendChild(link); link.click(); doc.body.removeChild(link);
        win.setTimeout(function () { win.URL.revokeObjectURL(url); }, 1000); message('\u0110\u00e3 xu\u1ea5t b\u00e1o c\u00e1o JSON; kh\u00f4ng ch\u1ee9a m\u00e3 phi\u00ean \u0111\u0103ng nh\u1eadp.'); return true;
    }
    function clearAudit() {
        if (op) return false;
        win.sessionStorage.removeItem(historyKey); showJournal(); message('\u0110\u00e3 x\u00f3a nh\u1eadt k\u00fd trong phi\u00ean; c\u00e1c b\u1ea3n kh\u00f4i ph\u1ee5c v\u1eabn \u0111\u01b0\u1ee3c gi\u1eef.'); return true;
    }
    frame.onload = loaded;
    showJournal();
    return {execute: execute, state: function(){return {configuration:Object.assign({}, configuration),read_times:Object.assign({}, reads),events:journal()};}, start: start, loaded: loaded, inspect: function () { return start('ppa', false, null, true); },
        navigate: navigate, exportReport: exportReport, clearAudit: clearAudit};
}));
