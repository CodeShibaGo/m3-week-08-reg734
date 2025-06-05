$(document).ready(function() {
    const $searchForm = $('#searchForm');
    const $searchInput = $('#searchInput');
    const $resultsContainer = $('#results');
    const $prevPageButton = $('#prevPage');
    const $nextPageButton = $('#nextPage');
    const $pageInfo = $('#pageInfo');
    const $pagination = $('.pagination');

    let currentPageToken = '';
    let nextPageToken = '';
    let prevPageToken = '';
    let currentPage = 1;

    // 初始化 Fancybox
    Fancybox.bind("[data-fancybox]", {
        // 自訂選項
    });

    // 假資料
    const mockData = {
        items: [
            {
                id: { videoId: 'dQw4w9WgXcQ' },
                snippet: {
                    title: '示例影片 1',
                    channelTitle: '示例頻道 1',
                    description: '這是一個示例影片描述。這是一個示例影片描述。這是一個示例影片描述。',
                    thumbnails: {
                        high: {
                            url: 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'
                        }
                    }
                }
            },
            {
                id: { videoId: 'jNQXAC9IVRw' },
                snippet: {
                    title: '示例影片 2',
                    channelTitle: '示例頻道 2',
                    description: '這是另一個示例影片描述。這是另一個示例影片描述。這是另一個示例影片描述。',
                    thumbnails: {
                        high: {
                            url: 'https://i.ytimg.com/vi/jNQXAC9IVRw/hqdefault.jpg'
                        }
                    }
                }
            }
        ]
    };

    // 搜尋功能
    async function searchVideos(pageToken = '') {
        const searchTerm = $searchInput.val().trim();
        if (!searchTerm) {
            alert('請輸入搜尋關鍵字');
            return;
        }

        const API_KEY = '你的api金鑰';
        let url = `https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=10&q=${encodeURIComponent(searchTerm)}&type=video&key=${API_KEY}`;
        
        if (pageToken) {
            url += `&pageToken=${pageToken}`;
        }

        try {
            const response = await fetch(url);
            const data = await response.json();
            
            // 更新分頁資訊
            nextPageToken = data.nextPageToken || '';
            prevPageToken = data.prevPageToken || '';
            
            // 更新按鈕狀態
            updatePaginationButtons(data);
            
            // 顯示結果
            displayResults(data);
        } catch (error) {
            console.error('Error:', error);
            alert('搜尋時發生錯誤，請稍後再試');
        }
    }

    // 顯示搜尋結果
    function displayResults(data) {
        $resultsContainer.empty();
        
        data.items.forEach(item => {
            const videoId = item.id.videoId;
            const thumbnailUrl = item.snippet.thumbnails.high.url;
            const title = item.snippet.title;
            const channelTitle = item.snippet.channelTitle;
            const description = item.snippet.description;

            const $videoCard = $(`
                <div class="video-card">
                    <a href="https://www.youtube.com/watch?v=${videoId}" 
                       data-fancybox 
                       data-type="iframe"
                       data-width="640"
                       data-height="360">
                        <img src="${thumbnailUrl}" alt="${title}" class="video-thumbnail">
                        <div class="video-info">
                            <h3 class="video-title">${title}</h3>
                            <p class="video-channel">${channelTitle}</p>
                            <p class="video-description">${description}</p>
                        </div>
                    </a>
                </div>
            `);

            $resultsContainer.append($videoCard);
        });
    }

    // 更新分頁按鈕狀態
    function updatePaginationButtons(data) {
        // 檢查是否有足夠的結果來顯示分頁
        const hasEnoughResults = data.items && data.items.length >= 10;
        
        if (hasEnoughResults) {
            $pagination.show();
            $prevPageButton.prop('disabled', !prevPageToken);
            $nextPageButton.prop('disabled', !nextPageToken);
            $pageInfo.text(`第 ${currentPage} 頁`);
        } else {
            $pagination.hide();
        }
    }

    // 下一頁
    function goToNextPage() {
        if (nextPageToken) {
            currentPageToken = nextPageToken;
            currentPage++;
            searchVideos(nextPageToken);
        }
    }

    // 上一頁
    function goToPrevPage() {
        if (prevPageToken) {
            currentPageToken = prevPageToken;
            currentPage--;
            searchVideos(prevPageToken);
        }
    }

    // 重置分頁
    function resetPagination() {
        currentPage = 1;
        currentPageToken = '';
        nextPageToken = '';
        prevPageToken = '';
        $pagination.hide();
    }

    // 表單提交事件
    $searchForm.on('submit', function(e) {
        e.preventDefault();
        resetPagination();
        searchVideos();
    });

    // 分頁按鈕事件
    $prevPageButton.on('click', goToPrevPage);
    $nextPageButton.on('click', goToNextPage);

    // 初始隱藏分頁
    $pagination.hide();
}); 