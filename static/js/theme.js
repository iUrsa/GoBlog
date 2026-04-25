(function() {
    // 获取保存的主题设置
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }

    // 更新主题图标
    function updateToggleIcons() {
        const stored = localStorage.getItem('theme');
        const sun = document.querySelector('.sun-icon');
        const moon = document.querySelector('.moon-icon');
        const btn = document.getElementById('theme-toggle');

        if (sun) sun.classList.toggle('hidden', stored !== 'light');
        if (moon) moon.classList.toggle('hidden', stored !== 'dark');

        if (btn) {
            const label = stored === 'dark' ? '深色' : stored === 'light' ? '浅色' : '跟随系统';
            btn.setAttribute('aria-label', `主题：${label}`);
        }
    }

    // 设置主题切换功能
    function setupToggle() {
        const btn = document.getElementById('theme-toggle');
        if (!btn) return;
        
        btn.addEventListener('click', () => {
            const stored = localStorage.getItem('theme');

            if (stored === 'light') {
                // 浅色 → 跟随系统
                localStorage.removeItem('theme');
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                document.documentElement.classList.toggle('dark', prefersDark);
            } else if (stored === 'dark') {
                // 深色 → 浅色
                localStorage.setItem('theme', 'light');
                document.documentElement.classList.remove('dark');
            } else {
                // 跟随系统 → 深色
                localStorage.setItem('theme', 'dark');
                document.documentElement.classList.add('dark');
            }

            updateToggleIcons();
        });
        updateToggleIcons();
    }

    // 初始化
    setupToggle();
})();
