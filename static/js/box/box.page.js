/**
 * 切分校对-前端html页面操作函数
 */
(function () {
  'use strict';

  $.box.onBoxChanged(function (box, reason, param) {
    if (['recovered', 'added', 'deleted', 'changed'].indexOf(reason) > -1) {
      $.page.updateHeadBoxKindNo();
    }
    if (reason === 'recovered') {
      // 更新已删除字框数量（注：只有在"我的修改"状态下才可以看见、恢复已删除字框，且无法修改其它字框）
      $('.hint .deleted .no').text($('.box.deleted').length);
    }
    if (reason === 'switch') {
      $.page.updateFootCharInfo(box);
    }
    if (['recovered', 'added', 'deleted', 'changed', 'redo', 'undo'].indexOf(reason) > -1) {
      $.box.canRedo && $.box.canRedo() ? $('#redo').removeClass('disabled') : $('#redo').addClass('disabled');
      $.box.canUndo && $.box.canUndo() ? $('#undo').removeClass('disabled') : $('#undo').addClass('disabled');
    }
    if (['redo', 'undo'].indexOf(reason) > -1) {
      let boxBtn = $('#toggle-' + box.boxType);
      if (!boxBtn.hasClass('active')) boxBtn.click();
      updateHeadBoxKindNo();
    }
  });

  let pStatus = {
    cut: {editBox: null, boxType: 'char'},      // 当前切分校对参数
    order: {noType: null, linkType: 'char'},    // 当前框序校对参数
  };

  $.page = {
    pStatus: pStatus,
    init: init,
    toggleNo: toggleNo,
    toggleLink: toggleLink,
    toggleMode: toggleMode,
    toggleCurHint: toggleCurHint,
    toggleCurShape: toggleCurShape,
    toggleCurBoxType: toggleCurBoxType,
    checkAndExport: checkAndExport,
    initHeadHintList: initHeadHintList,
    updateHeadBoxKindNo: updateHeadBoxKindNo,
    updateFootHintNo: updateFootHintNo,
    updateFootCharInfo: updateFootCharInfo,

  };

  function init(p) {
    // 1. 初始化
    $.box.initSvg(p.holder, p.imgUrl, parseInt(p.width || 0), parseInt(p.height || 0), p.showMode);
    $.box.setParam({userId: p.userId, readonly: p.readonly});
    // 2. 设置boxes
    $.box.setBoxes({
      chars: p.chars || [],
      blocks: p.blocks || [],
      columns: p.columns || [],
      images: p.images || [],
    });
    if (p.curBoxType) {
      $.box.setCurBoxType(p.curBoxType);
      $.box.switchBoxType(p.curBoxType, true);
    } else {
      $($.box.data.holder).addClass('hide-all');
    }
    // 3. 设置图片
    $.box.toggleImage(p.showImage || true);
    $.box.setImageOpacity(p.blurImage || 0.2);
    $.box.bindCut && $.box.bindCut(p);
    $.box.bindOrder && $.box.bindOrder();
    if (p.mayWrong) $.box.eStatus.mayWrong = p.mayWrong;
    if (p.userLinks) $.box.oStatus.userLinks = p.userLinks;
    if ($.box.eStatus) {
      // 4. 设置字框大小窄扁等属性
      $.box.initCharKind && $.box.initCharKind();
      updateHeadBoxKindNo();
      // 5. 设置导航条中操作历史
      initHeadHintList();
    }
    // 6. 设置文本
    if (p.txtHolder) {
      $(p.holder).addClass('show-current');
      $.box.initTxt(p.txtHolder, 'txt', p.useTooTips);
      initHeadTxtList();
    }
  }

  function checkAndExport() {
    // check
    if ($.box.isCutMode()) {
      let r = $.box.checkBoxes();
      if (!r.status) return {status: false};
      $.box.reorderBoxes();
      $.box.loadUserLinks();
    } else {
      let r = $.box.checkLinks();
      if (!r.status) {
        $.page.toggleLink(r.errorBoxType, true);
        return {status: false};
      }
      $.box.updateNoByLinks(r.links);
      $.box.updateUserLinks();
    }
    // export
    let ret = $.box.exportSubmitData();
    ret['user_links'] = $.box.oStatus.userLinks;
    ret['status'] = true;
    return ret;
  }

  function toggleMode(mode) {
    if (mode === $.box.status.boxMode) return;
    if (mode === 'order') { // 从切分校对切换为字序校对
      // 记录切分状态
      pStatus.cut.boxType = $.box.status.curBoxType;
      // 进入字序校对
      if ($.box.cStatus.hasChanged) {
        let r = $.box.checkBoxes();
        if (!r.status) return;
        $.box.reorderBoxes();
        $.box.loadUserLinks();
        // $.box.cStatus.hasChanged = false;
        $.box.drawLink(true);
      }
      $('#toggle-order').addClass('hide');
      $('#toggle-cut').removeClass('hide');
      $('.m-header .left .title').text('字序');
      toggleCurBoxType(null, false);
      toggleNo(pStatus.order.noType, true);
      toggleLink(pStatus.order.linkType || 'char', true, true);
    } else { // 从字序校对切换为切分校对
      // 检查并更新线序link、更新序号no
      if ($.box.oStatus.hasChanged) {
        let r = $.box.checkLinks();
        if (!r.status) return;
        $.box.updateNoByLinks(r.links);
        $.box.updateUserLinks();
        // $.box.oStatus.hasChanged = false;
      }
      // 记录字序状态
      pStatus.order.noType = $.box.status.curNoType;
      pStatus.order.linkType = $.box.oStatus.curLinkType;
      toggleNo(null, false);
      toggleLink(null, false);
      // 进入切分校对
      $('#toggle-cut').addClass('hide');
      $('#toggle-order').removeClass('hide');
      $('.m-header .left .title').text('切分');
      toggleCurBoxType(pStatus.cut.boxType, true);
    }
    $('.m-toolbar').removeClass('cut-mode order-mode').addClass(mode + '-mode');
    $($.box.data.holder).removeClass('cut-mode order-mode').addClass(mode + '-mode');
    $.box.status.boxMode = mode;
  }

  function toggleNo(boxType, show) {
    $('.toggle-no').removeClass('active');
    show && $('#toggle-no-' + boxType).addClass('active');
    $.box.toggleNo(boxType, show);
  }

  function toggleLink(boxType, show, navFirst) {
    $('.toggle-link').removeClass('active');
    show && $('#toggle-link-' + boxType).addClass('active');
    $.box.toggleLink(boxType, show);
    navFirst && $.box.switchCurBox($.box.findFirstBox(boxType));
  }

  function toggleCurShape(shape, show) {
    $('.toggle-shape').removeClass('active');
    show && $('#toggle-' + shape).addClass('active');
    let holder = $($.box.data.holder);
    let names = holder.attr('class').split(' ');
    holder.attr('class', names.filter((n) => n.length && n.indexOf('shape-') < 0).join(' '));
    show && holder.addClass('shape-' + shape);
    if ($.box.cStatus.isMulti) $.box.selectBoxesByShape(shape, !show);
  }

  function toggleCurBoxType(boxType, show) {
    $('.toggle-box').removeClass('active');
    show && $('#toggle-' + boxType).addClass('active');
    $.box.switchBoxType(boxType || '', show);
    show && $.box.switchCurBox(null);
    show && updateHeadBoxKindNo();
    updateFootHintNo();
  }

  function toggleCurHint(type, value, hide) {
    if (hide) {
      $.box.hideAllHint();
      $('.m-footer .hint-info').addClass('hide');
      toggleCurBoxType(pStatus.cut.boxType, true);
    } else if (type === 'init') {
      $.box.showInitHint();
      $('.m-footer .hint-info').addClass('hide');
    } else {
      if (type === 'comb') $.box.showCombHint();
      else if (type === 'my') $.box.showMyHint(value);
      else if (type === 'user') $.box.showUserHint(value);
      else if (type === 'time') $.box.showTimeHint(value);
      updateFootHintNo();
      $('.m-footer .hint-info').removeClass('hide');
      // let boxTypes = $.box.eStatus.hint.boxTypes;
      // toggleCurBoxType(boxTypes.length === 1 ? boxTypes[0] : 'all', true);
    }
  }

  function updateHeadBoxKindNo() {
    let boxType = $.box.status.curBoxType;
    let no = $.box.getBoxKindNo && $.box.getBoxKindNo() || {};
    let or1 = 'block,column,char'.indexOf(boxType) > -1 ? 0 : '';
    $('#toggle-white .s-count').text(no.total || or1);
    $('#toggle-opacity .s-count').text(no.total || or1);
    $('#toggle-overlap .s-count').text(no.overlap || or1);
    let or2 = boxType === 'char' ? 0 : '';
    $('#toggle-flat .s-count').text(no.flat || or2);
    $('#toggle-large .s-count').text(no.large || or2);
    $('#toggle-small .s-count').text(no.small || or2);
    $('#toggle-narrow .s-count').text(no.narrow || or2);
    $('#toggle-mayWrong .s-count').text(no.mayWrong || or2);
  }

  function initHeadHintList() {
    if (!$('#hint-list').length) return;
    $.box.initUserAndTime();
    let html = '';
    if ($.box.eStatus.users.length) {
      html += '<li class="divider"></li>';
      $.box.eStatus.users.forEach(function (item) {
        let a = `<a>${item.username} 的修改</a>`;
        html += `<li class="user-hint hint" title="${item.user_id}">${a}</li>`;
      });
    }
    if ($.box.eStatus.times.length) {
      html += '<li class="divider"></li>';
      $.box.eStatus.times.forEach(function (item) {
        let a = `<a>${item.create_time + '@' + item.username}</a>`;
        html += `<li class="time-hint hint" title="${item.create_time}">${a}</li>`;
      });
    }
    if (html) $('#hint-list').append(html);
  }

  function initHeadTxtList() {
    ['cmb_txt', 'ocr_txt', 'ocr_col', 'cmp_txt'].forEach((txtType) => {
      if (!$.box.hasTxtType(txtType)) $('.toggle-txt#' + txtType).addClass('hide');
    });
    if (!$('.toggle-txt:not(.hide)').length) $('#toggle-txts').addClass('hide');
  }

  function updateFootHintNo() {
    if (!$.box.getHintNo) return;
    let no = $.box.getHintNo();
    $('.m-footer .hint-info .added .s-no').text(no.added || 0);
    $('.m-footer .hint-info .deleted .s-no').text(no.deleted || 0);
    $('.m-footer .hint-info .changed .s-no').text(no.changed || 0);
  }

  function updateFootCharInfo(box) {
    if (box) {
      let t = {char: '字框', column: '列框', block: '栏框', image: '图框'};
      $('.m-footer .char-name').text(`${t[box.boxType]}#${box.cid}#${box[box.boxType + '_id'] || ''}`);
      let info = `${box.txt || box['ocr_txt'] || ''}${box.readonly ? '/只读' : ''}`;
      $('.m-footer .char-id').text(info);
    } else {
      $('.m-footer .char-name').text('未选中');
      $('.m-footer .char-id').text('');
    }
  }

}());