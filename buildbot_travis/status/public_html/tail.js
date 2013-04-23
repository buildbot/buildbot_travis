/**
 * Author: Richard Mitchell <richard.mitchell@isotoma.com>
 * Automatically follow the tail of a page as it's loading.
 * Originally written as a bookmarklet, hence the lack of jQuery.
 */

window.autoscroll = function (autostart, headless) {
  window.autoscroll.headless = !!headless;
  if (!window.autoscroll.headless) {
    var container = document.createElement('div');
    container.style.position = 'fixed';
    container.style.height = '50px';
    container.style.width = '100px';
    container.style.bottom = '0';
    container.style.right = '0';
    container.style.backgroundColor = '#F6F6F6';
    var form = document.createElement('form');
    form.action='#';
    form.onsubmit=function (e){e.preventDefault();};
    window.autoscroll.toggleButton = document.createElement('input');
    window.autoscroll.toggleButton.type='button';
    window.autoscroll.toggleButton.value='tail on';
    window.autoscroll.toggleButton.onclick=window.autoscroll.toggle;
    window.autoscroll.toggleButton.style.height='50px';
    window.autoscroll.toggleButton.style.width='100px';
    form.appendChild(window.autoscroll.toggleButton);
    container.appendChild(form);
    var body = document.getElementsByTagName('body')[0];
    body.insertBefore(container, body.firstChild);
    window.autoscroll.running=false;
  }
  if (window.autoscroll.headless || !!autostart) {
    window.autoscroll.start();
  }
};
window.autoscroll.start = function () {
  if (!window.autoscroll.headless) {
    window.autoscroll.toggleButton.value='tail off';
  }
  window.autoscroll.run();
};
window.autoscroll.run = function () {
  var top = Math.min(Math.pow(2, 30), Number.MAX_VALUE);
  window.scrollTo(window.pageXOffset, top);
  if (document.readyState==='loading' ||
      document.readyState==='interactive') {
    window.autoscroll.timeoutHandle = window.setTimeout(window.autoscroll.run, 100);
    window.autoscroll.running=true;
  } else {
    window.autoscroll.stop();
  }
};
window.autoscroll.stop = function () {
  window.clearTimeout(window.autoscroll.timeoutHandle);
  window.autoscroll.running=false;
  if (!window.autoscroll.headless) {
    window.autoscroll.toggleButton.value='tail on';
  }
};
window.autoscroll.toggle = function () {
  if (window.autoscroll.running) {
    window.autoscroll.stop();
  } else {
    window.autoscroll.start();
  }
};
