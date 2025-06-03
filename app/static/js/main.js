// 主要JavaScript功能
$(document).ready(function() {
    // 初始化所有功能
    initializeApp();
});

function initializeApp() {
    // 初始化AOS动画
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            once: true,
            offset: 100
        });
    }
    
    // 初始化Moment.js中文
    if (typeof moment !== 'undefined') {
        moment.locale('zh-cn');
    }
    
    // 初始化各种功能
    initializeTheme();
    initializeNavigation();
    initializeSearch();
    initializeBackToTop();
    initializeTooltips();
    initializeLazyLoading();
    loadWeatherInfo();
    loadSiteStats();
    loadVisitorInfo();
    
    // 绑定事件
    bindEvents();
}

// 主题切换功能
function initializeTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const html = document.documentElement;
    
    // 从localStorage获取主题设置
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-bs-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = html.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            html.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }
    
    function updateThemeIcon(theme) {
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
}

// 导航栏功能
function initializeNavigation() {
    // 滚动时改变导航栏样式
    $(window).scroll(function() {
        const navbar = $('.navbar');
        if ($(window).scrollTop() > 50) {
            navbar.addClass('navbar-scrolled');
        } else {
            navbar.removeClass('navbar-scrolled');
        }
    });
    
    // 移动端导航菜单自动关闭
    $('.navbar-nav .nav-link').on('click', function() {
        $('.navbar-collapse').collapse('hide');
    });
}

// 搜索功能
function initializeSearch() {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/blog?search=${encodeURIComponent(query)}`;
            }
        });
    }
    
    // 搜索建议功能
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    showSearchSuggestions(query);
                }, 300);
            } else {
                hideSearchSuggestions();
            }
        });
    }
}

// 搜索建议
function showSearchSuggestions(query) {
    $.get(`/api/search?q=${encodeURIComponent(query)}&page=1`)
        .done(function(response) {
            if (response.success && response.data.posts.length > 0) {
                const suggestions = response.data.posts.slice(0, 5);
                displaySearchSuggestions(suggestions);
            }
        });
}

function displaySearchSuggestions(suggestions) {
    // 创建建议下拉框
    let dropdown = $('#searchSuggestions');
    if (dropdown.length === 0) {
        dropdown = $('<div id="searchSuggestions" class="search-suggestions"></div>');
        $('#searchInput').parent().append(dropdown);
    }
    
    let html = '';
    suggestions.forEach(post => {
        html += `
            <div class="suggestion-item" onclick="window.location.href='/post/${post.slug}'">
                <div class="suggestion-title">${post.title}</div>
                <div class="suggestion-summary">${post.summary}</div>
            </div>
        `;
    });
    
    dropdown.html(html).show();
}

function hideSearchSuggestions() {
    $('#searchSuggestions').hide();
}

// 返回顶部按钮
function initializeBackToTop() {
    const backToTopBtn = document.getElementById('backToTop');
    
    if (backToTopBtn) {
        $(window).scroll(function() {
            if ($(window).scrollTop() > 300) {
                $(backToTopBtn).fadeIn();
            } else {
                $(backToTopBtn).fadeOut();
            }
        });
        
        backToTopBtn.addEventListener('click', function() {
            $('html, body').animate({scrollTop: 0}, 600);
        });
    }
}

// 工具提示
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// 懒加载
function initializeLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// 加载天气信息
function loadWeatherInfo() {
    $.get('/api/weather')
        .done(function(response) {
            if (response.success) {
                const weather = response.data;
                $('#weatherTemp').text(`${weather.temperature}°C`);
                $('#weatherDesc').text(weather.description);
                $('#weatherIcon').html(`<i class="fas fa-cloud-sun"></i>`);
            }
        })
        .fail(function() {
            $('#weatherTemp').text('天气信息不可用');
            $('#weatherDesc').text('');
        });
}

// 加载网站统计
function loadSiteStats() {
    $.get('/api/stats')
        .done(function(response) {
            if (response.success) {
                const stats = response.data;
                $('#totalPosts').text(stats.total_posts || 0);
                $('#totalVisitors').text(stats.total_visitors || 0);
                $('#totalViews').text(stats.total_views || 0);
            }
        });
}

// 加载访客信息
function loadVisitorInfo() {
    $.get('/api/visitor-info')
        .done(function(response) {
            if (response.success) {
                const visitor = response.data;
                let locationText = '未知位置';
                
                if (visitor.city && visitor.country) {
                    locationText = `${visitor.city}, ${visitor.country}`;
                    if (visitor.distance) {
                        locationText += ` (距离博主 ${visitor.distance}km)`;
                    }
                }
                
                $('#visitorLocation').text(locationText);
            }
        })
        .fail(function() {
            $('#visitorLocation').text('位置信息不可用');
        });
}

// 绑定事件
function bindEvents() {
    // 图片点击放大
    $('img').on('click', function() {
        if ($(this).hasClass('img-fluid')) {
            showImageModal(this.src, this.alt);
        }
    });
    
    // 代码复制功能
    $('pre code').each(function() {
        const code = $(this);
        const copyBtn = $('<button class="copy-btn btn btn-sm btn-outline-secondary">复制</button>');
        code.parent().css('position', 'relative').append(copyBtn);
        
        copyBtn.on('click', function() {
            navigator.clipboard.writeText(code.text()).then(function() {
                copyBtn.text('已复制').addClass('btn-success').removeClass('btn-outline-secondary');
                setTimeout(() => {
                    copyBtn.text('复制').removeClass('btn-success').addClass('btn-outline-secondary');
                }, 2000);
            });
        });
    });
    
    // 表单验证
    $('.needs-validation').on('submit', function(e) {
        if (!this.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
}

// 显示图片模态框
function showImageModal(src, alt) {
    const modal = $(`
        <div class="modal fade" id="imageModal" tabindex="-1">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${alt || '图片预览'}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <img src="${src}" class="img-fluid" alt="${alt}">
                    </div>
                </div>
            </div>
        </div>
    `);
    
    $('body').append(modal);
    modal.modal('show');
    
    modal.on('hidden.bs.modal', function() {
        modal.remove();
    });
}

// 通用工具函数
const Utils = {
    // 格式化日期
    formatDate: function(date, format = 'YYYY-MM-DD') {
        if (typeof moment !== 'undefined') {
            return moment(date).format(format);
        }
        return new Date(date).toLocaleDateString();
    },
    
    // 截断文本
    truncateText: function(text, length = 100) {
        if (text.length <= length) return text;
        return text.substring(0, length) + '...';
    },
    
    // 防抖函数
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // 节流函数
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // 显示通知
    showNotification: function(message, type = 'info') {
        const notification = $(`
            <div class="alert alert-${type} alert-dismissible fade show notification" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        
        $('body').append(notification);
        
        setTimeout(() => {
            notification.alert('close');
        }, 5000);
    },
    
    // 加载状态
    showLoading: function(element) {
        $(element).html('<span class="loading"></span> 加载中...');
    },
    
    hideLoading: function(element, originalText) {
        $(element).html(originalText);
    }
};

// 全局错误处理
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
});

// AJAX错误处理
$(document).ajaxError(function(event, xhr, settings, thrownError) {
    console.error('AJAX Error:', thrownError);
    if (xhr.status === 404) {
        Utils.showNotification('请求的资源不存在', 'warning');
    } else if (xhr.status >= 500) {
        Utils.showNotification('服务器错误，请稍后重试', 'danger');
    }
});

// 导出到全局
window.Utils = Utils;
