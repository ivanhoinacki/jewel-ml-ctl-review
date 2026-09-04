/* Jewel ML loader. Clients paste this once, just before </body>.
   Requires: <div id="jml-complete-the-look" data-integration="YOUR_ID" data-sku="CURRENT_SKU"></div> */
(function () {
  var container = document.getElementById('jml-complete-the-look');
  if (!container || !container.dataset.integration || !container.dataset.sku) return;

  var s = document.createElement('script');
  s.src = 'https://cdn.jewelml.io/widgets/v1/jewel.js';
  s.onload = function () {
    window.jewelml.mountCompleteTheLook(container, container.dataset.integration, container.dataset.sku);
  };
  document.head.appendChild(s);
})();
