"""
Vision Processing Module using PyMuPDF

页面渲染、图片提取和视觉理解
"""

import fitz  # PyMuPDF


class VisionProcessor:
    """视觉处理器 - 使用PyMuPDF处理PDF图片"""

    def __init__(self, pdf_path):
        """初始化视觉处理器"""
        self.pdf_path = str(pdf_path)
        self._doc = None

    def _get_doc(self):
        if self._doc is None:
            self._doc = fitz.open(self.pdf_path)
        return self._doc

    def close(self):
        if self._doc is not None:
            self._doc.close()
            self._doc = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def render_pages(self, dpi=150):
        """
        将PDF页面转换为图片

        Args:
            dpi: 分辨率（默认150）

        Returns:
            list[dict]: 每页信息，包含：
                - page_num: 页码（0-indexed）
                - image_bytes: PNG字节数据
                - width: 宽度（像素）
                - height: 高度（像素）
        """
        doc = self._get_doc()
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            pixmap = page.get_pixmap(matrix=matrix)
            pages.append({
                'page_num': page_num,
                'image_bytes': pixmap.tobytes('png'),
                'width': pixmap.width,
                'height': pixmap.height,
            })

        return pages

    def extract_images(self, image_mode='extract'):
        """
        提取页面中的嵌入图片

        Args:
            image_mode: 'disabled' | 'description-only' | 'extract'

        Returns:
            list[dict]: 图片列表，每项包含：
                - page_num: 页码（0-indexed）
                - xref: PyMuPDF图片引用ID
                - image_bytes: 图片字节数据
                - width: 宽度（像素）
                - height: 高度（像素）
                - bbox: 在页面中的位置 (x0, y0, x1, y1)，None表示未找到
                - ext: 图片格式（png/jpeg等）
        """
        if image_mode == 'disabled':
            return []

        doc = self._get_doc()
        images = []
        seen_xrefs = set()  # 避免跨页重复提取同一图片资源

        for page_num in range(len(doc)):
            page = doc[page_num]
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)

                base_image = doc.extract_image(xref)
                bbox = self._get_image_bbox(page, xref)

                images.append({
                    'page_num': page_num,
                    'xref': xref,
                    'image_bytes': base_image['image'],
                    'width': base_image['width'],
                    'height': base_image['height'],
                    'bbox': bbox,
                    'ext': base_image['ext'],
                })

        return images

    def _get_image_bbox(self, page, xref):
        """获取图片在页面中的第一个边界框"""
        rects = page.get_image_rects(xref)
        if rects:
            r = rects[0]
            return (r.x0, r.y0, r.x1, r.y1)
        return None

    def identify_image_regions(self):
        """
        识别各页中的图片区域（不提取图片数据）

        Returns:
            list[dict]: 区域列表，每项包含：
                - page_num: 页码
                - xref: 图片引用ID
                - bbox: 坐标 (x0, y0, x1, y1)
                - width: 宽度
                - height: 高度
        """
        doc = self._get_doc()
        regions = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                width = img_info[2]
                height = img_info[3]
                bbox = self._get_image_bbox(page, xref)

                regions.append({
                    'page_num': page_num,
                    'xref': xref,
                    'bbox': bbox,
                    'width': width,
                    'height': height,
                })

        return regions
