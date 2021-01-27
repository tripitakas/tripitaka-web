/**
 @desc 聚类相关操作
 */
//----------------------快捷键----------------------
$.mapKey('a', () => $('#bat-select').click());
$.mapKey('v', () => $('#do-multi').click());
$.mapKey('z', () => $('#de-multi').click());
$.mapKey('x', () => $('#un-multi').click());
$.mapKey('1', () => $('#toggle-filter-panel').click());
$.mapKey('2', () => $('#toggle-char-info').click());
$.mapKey('3', () => $('#toggle-column-panel').click());
$.mapKey('4', () => $('#toggle-proof-panel').click());
$.mapKey('5', () => $('#toggle-proof-color').click());
$.mapKey('esc', () => togglePanels(true));
$.mapKey('left', () => $('.char-item.current').prev().find('.char-img').click());
$.mapKey('right', () => $('.char-item.current').next().find('.char-img').click());

//----------------------初始化----------------------
function togglePanels(init) {
  $('#toggle-filter-panel').toggleClass('active', init ? true : getStorage('clusterFilterPanel', true));
  $('.m-panel').toggleClass('hide', init ? false : !getStorage('clusterFilterPanel', true));
  $('#toggle-char-info').toggleClass('active', init ? true : getStorage('clusterCharInfo', true));
  $('.char-info, .char-check').toggleClass('hide', init ? false : !getStorage('clusterCharInfo', true));
  $('#toggle-column-panel').toggleClass('active', init ? true : getStorage('clusterColumnPanel', true));
  $('.column-panel').toggleClass('hide', init ? false : !getStorage('clusterColumnPanel', true));
  $('#toggle-proof-panel').toggleClass('active', init ? true : getStorage('clusterProofPanel', true));
  $('.proof-panel').toggleClass('hide', init ? false : !getStorage('clusterProofPanel', true));
  $('#toggle-proof-color').toggleClass('active', init ? true : getStorage('clusterProofColor', true));
  $('.char-panel').toggleClass('show-mark', init ? true : getStorage('clusterProofColor', true));
}

//----------------------左侧导航：排序及过滤----------------------
$('#btn-cc-up').on('click', function () {
  location.href = toggleQueryString('order', 'cc', !$(this).hasClass('active'));
});
$('#btn-cc-down').on('click', function () {
  location.href = toggleQueryString('order', '-cc', !$(this).hasClass('active'));
});
$('#btn-lc-up').on('click', function () {
  location.href = toggleQueryString('order', 'lc', !$(this).hasClass('active'));
});
$('#btn-lc-down').on('click', function () {
  location.href = toggleQueryString('order', '-lc', !$(this).hasClass('active'));
});
$('#btn-sc-2').on('click', function () {
  location.href = toggleQueryString('sc', '2', !$(this).hasClass('active'));
});
$('#btn-sc-1').on('click', function () {
  location.href = toggleQueryString('sc', '1', !$(this).hasClass('active'));
});
$('#btn-sc-0').on('click', function () {
  location.href = toggleQueryString('sc', '0', !$(this).hasClass('active'));
});
$('#btn-vague').on('click', function () {
  location.href = toggleQueryString('is_vague', 'true', !$(this).hasClass('active'));
});
$('#btn-un-vague').on('click', function () {
  location.href = toggleQueryString('is_vague', 'false', !$(this).hasClass('active'));
});
$('#btn-deform').on('click', function () {
  location.href = toggleQueryString('is_deform', 'true', !$(this).hasClass('active'));
});
$('#btn-un-deform').on('click', function () {
  location.href = toggleQueryString('is_deform', 'false', !$(this).hasClass('active'));
});
$('#btn-certain').on('click', function () {
  location.href = toggleQueryString('uncertain', 'false', !$(this).hasClass('active'));
});
$('#btn-uncertain').on('click', function () {
  location.href = toggleQueryString('uncertain', 'true', !$(this).hasClass('active'));
});
$('#btn-has-remark').on('click', function () {
  location.href = toggleQueryString('remark', 'true', !$(this).hasClass('active'));
});
$('#btn-no-remark').on('click', function () {
  location.href = toggleQueryString('remark', 'false', !$(this).hasClass('active'));
});
$('#btn-submitted').on('click', function () {
  location.href = toggleQueryString('submitted', 'true', !$(this).hasClass('active'));
});
$('#btn-un-submitted').on('click', function () {
  location.href = toggleQueryString('submitted', 'false', !$(this).hasClass('active'));
});
$('#btn-updated').on('click', function () {
  location.href = toggleQueryString('updated', 'all', !$(this).hasClass('active'));
});
$('#btn-un-updated').on('click', function () {
  location.href = toggleQueryString('updated', 'un', !$(this).hasClass('active'));
});
$('#btn-my-updated').on('click', function () {
  location.href = toggleQueryString('updated', 'my', !$(this).hasClass('active'));
});
$('#btn-other-updated').on('click', function () {
  location.href = toggleQueryString('updated', 'other', !$(this).hasClass('active'));
});
$('#btn-unauthorized').on('click', function () {
  location.href = toggleQueryString('authorized', 'un', !$(this).hasClass('active'));
});


//----------------------顶部导航----------------------
// 置信度过滤
$('#btn-filter').on('click', function () {
  let start = $('#filter-start').val();
  if (start && start.match(/^(0\.\d+|0|1|1\.0)$/) === null)
    return showTips('提示', '起始值不符合要求', 3000);
  let end = $('#filter-end').val();
  if (end && end.match(/^(0\.\d+|0|1|1\.0)$/) === null)
    return showTips('提示', '终止值不符合要求', 3000);
  if (!start.length && !end.length)
    return showTips('提示', '请输入起始值或终止值', 3000);
  if (start.length && !end.length) {
    location.href = setQueryString('cc', '>=' + start);
  } else if (end.length && !start.length) {
    location.href = setQueryString('cc', '<=' + end);
  } else {
    location.href = setQueryString('cc', start + ',' + end);
  }
});

// 全部选择
$('#bat-select').on('click', function () {
  $(this).toggleClass('active');
  if ($(this).hasClass('active')) {
    $('.char-check :checkbox').prop('checked', true);
  } else {
    $('.char-check :checkbox').removeAttr('checked');
  }
});

// 多选模式-鼠标滑选
$('.toggle-multi').on('click', function () {
  $('.toggle-multi').removeClass('active');
  $(this).addClass('active');
  if ($(this).attr('id') === 'do-multi') {
    bsShow('', '鼠标滑选 / 正选 已打开', 'info', 800);
  } else if ($(this).attr('id') === 'de-multi') {
    bsShow('', '鼠标滑选 / 反选 已打开', 'info', 800);
  }
});

// 鼠标滑选
$(document).on('mouseenter', '.char-item', function () {
  let id = $('.toggle-multi.active').attr('id');
  if (id === 'do-multi') {
    $(this).find(':checkbox').prop('checked', true);
  } else if (id === 'de-multi') {
    $(this).find(':checkbox').removeAttr('checked');
  }
});

// 显隐排序过滤
$('#toggle-filter-panel').on('click', function () {
  $(this).toggleClass('active');
  setStorage('clusterFilterPanel', $(this).hasClass('active'));
  $('.m-panel').toggleClass('hide', !$(this).hasClass('active'));
});
// 显隐字图信息
$('#toggle-char-info').on('click', function () {
  $(this).toggleClass('active');
  setStorage('clusterCharInfo', $(this).hasClass('active'));
  $('.char-info, .char-check').toggleClass('hide', !$(this).hasClass('active'));
});
// 显隐字框列图
$('#toggle-column-panel').on('click', function () {
  $(this).toggleClass('active');
  setStorage('clusterColumnPanel', $(this).hasClass('active'));
  $('.column-panel').toggleClass('hide', !$(this).hasClass('active'));
});
// 显隐校对面板
$('#toggle-proof-panel').on('click', function () {
  $(this).toggleClass('active');
  setStorage('clusterProofPanel', $(this).hasClass('active'));
  $('.proof-panel').toggleClass('hide', !$(this).hasClass('active'));
});
// 显隐校对颜色
$('#toggle-proof-color').on('click', function () {
  $(this).toggleClass('active');
  setStorage('clusterProofColor', $(this).hasClass('active'));
  $('.char-panel').toggleClass('show-mark', $(this).hasClass('active'));
});

// 检索异体字
$('#search-variant').on('keydown', function (event) {
  let keyCode = event.keyCode || event.which;
  if (keyCode === 13) {
    let q = $(this).val().trim();
    if (q.length) window.open('http://hanzi.lqdzj.cn/variant_search?q=' + q, '_blank');
  }
});
$('#icon-search').on('click', function () {
  let q = $('#search-variant').val().trim();
  if (q.length) window.open('http://hanzi.lqdzj.cn/variant_search?q=' + q, '_blank');
});


//----------------------左侧字图----------------------
// 切换字种
$(document).on('click', '.txt-kind', function () {
  let txt = $(this).attr('data-value') || $(this).text().trim();
  location.href = txt ? deleteParam(setQueryString('txt', txt), 'page') : location.pathname;
});

// 切换字图
$(document).on('click', '.char-items .char-item', function () {
  $('.char-item.current').removeClass('current');
  $(this).addClass('current');
  let ch = $.cluster.status.chars[$(this).attr('data-value')];
  $.cluster.switchCurChar(ch);
  $.charTxt.setChar(ch);
});

// 选中字图
$(document).on('click', '.char-item .char-info, .char-item .char-check', function () {
  $(this).parent().find(':checkbox').click();
});

$(document).on('click', '.char-check input', function (e) {
  e.stopPropagation();
});


//----------------------中间列图----------------------
// 缩小图片
$('#zoom-out').on('click', function () {
  $.box.zoomImg(null, 0.9);
});

// 放大图片
$('#zoom-in').on('click', function () {
  $.box.zoomImg(null, 1.1);
});

// 提交字框修改
$('#submit-box').on('click', function () {
  if ($(this).hasClass('disabled')) return;
  let char = $.cluster.exportSubmitData();
  postApi(`/page/char/box/${char.name}`, {data: {pos: char}}, function (res) {
    bsShow('', '保存成功！', 'info', 1000);
    $.charTxt.setBoxLogs(res['box_logs']);
    $.cluster.status.curChar['box_logs'] = res['box_logs'];
  });
});


//----------------------底部查看----------------------
// 查看page
$('.m-footer .page-name').on('click', function () {
  if ($(this).hasClass('disabled')) return;
  let url = '/page/' + $(this).text();
  let charName = $('.m-footer .char-name').text();
  if (charName && charName.length && charName !== '未选中') {
    url += '?cid=' + charName.split('_').pop();
  }
  window.open(url, '_blank');
});

// 查看char
$('.m-footer .char-name').on('click', function () {
  let charName = $(this).text();
  if ($(this).hasClass('disabled') || charName === '未选中') return;
  window.open('/char/' + charName, '_blank');
});
