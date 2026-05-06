(function () {
  document.addEventListener('DOMContentLoaded', function () {
    // Show inline validation when a number input has a negative value.
    function getFeedbackEl(el) {
      if (!el || !el.parentNode) return null;
      const next = el.nextElementSibling;
      if (next && next.classList && next.classList.contains('negative-feedback')) return next;
      const div = document.createElement('div');
      div.className = 'negative-feedback text-danger small';
      div.style.display = 'none';
      if (el.parentNode) el.parentNode.insertBefore(div, el.nextSibling);
      return div;
    }

    function validate(el) {
      if (!el || el.type !== 'number') return;
      const fb = getFeedbackEl(el);
      const v = el.value;
      // allow empty or single '-' while typing; don't show message yet
      if (v === '' || v === '-') {
        if (fb) fb.style.display = 'none';
        el.classList.remove('is-invalid');
        el.removeAttribute('aria-invalid');
        delete el.dataset.invalidNegative;
        return;
      }
      const n = Number(v);
      if (!isNaN(n) && n < 0) {
        if (fb) {
          fb.textContent = 'Không được nhập giá trị âm.';
          fb.style.display = 'block';
        }
        el.classList.add('is-invalid');
        el.setAttribute('aria-invalid', 'true');
        el.dataset.invalidNegative = '1';
      } else {
        if (fb) fb.style.display = 'none';
        el.classList.remove('is-invalid');
        el.removeAttribute('aria-invalid');
        delete el.dataset.invalidNegative;
      }
    }

    function attach(el) {
      try {
        if (!el) return;
        if (!el.hasAttribute('min')) el.setAttribute('min', '0');
        validate(el);
        el.addEventListener('input', function () { validate(el); });
        el.addEventListener('blur', function () { validate(el); });
      } catch (e) {
        // ignore
      }
    }

    document.querySelectorAll('input[type=number]').forEach(attach);

    // Observe dynamically added inputs
    try {
      const mo = new MutationObserver(function (mutations) {
        mutations.forEach(function (m) {
          m.addedNodes.forEach(function (node) {
            if (!node || node.nodeType !== 1) return;
            if (node.matches && node.matches('input[type=number]')) attach(node);
            if (node.querySelectorAll) node.querySelectorAll('input[type=number]').forEach(attach);
          });
        });
      });
      mo.observe(document.body, { childList: true, subtree: true });
    } catch (e) {
      // MutationObserver may not be available in old browsers; that's fine.
    }

    // Prevent submit if any number inputs contain negative values.
    document.addEventListener('submit', function (e) {
      const form = e.target;
      if (!form || !form.querySelectorAll) return;
      const invalid = [];
      form.querySelectorAll('input[type=number]').forEach(function (el) {
        const v = el.value;
        if (v !== '' && !isNaN(Number(v)) && Number(v) < 0) invalid.push(el);
      });
      if (invalid.length) {
        e.preventDefault();
        try { invalid[0].focus(); } catch (err) {}
        alert('Các trường số không được phép nhập giá trị âm. Vui lòng sửa các trường đỏ trước khi gửi.');
      }
    }, true);
  });
})();
