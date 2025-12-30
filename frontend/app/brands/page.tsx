"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  brandApi,
  BrandSummary,
  BrandCreate,
  Brand,
  Product,
  ProductCreate,
  Ingredient,
  ProductCategory,
  SkinType,
  SkinConcern,
  IngredientCategory,
  TextureType,
  FinishType,
} from "@/lib/api";
import {
  Plus,
  Building2,
  Package,
  Pencil,
  Trash2,
  ChevronRight,
  X,
  Loader2,
  Users,
  Sparkles,
  Tag,
  Beaker,
  Droplets,
  ChevronDown,
  ChevronUp,
  Star,
  Upload,
  Image as ImageIcon,
} from "lucide-react";
import Image from "next/image";

export default function BrandsPage() {
  const queryClient = useQueryClient();
  const [selectedBrandId, setSelectedBrandId] = useState<string | null>(null);
  const [isCreateBrandOpen, setIsCreateBrandOpen] = useState(false);
  const [isEditBrandOpen, setIsEditBrandOpen] = useState(false);
  const [isCreateProductOpen, setIsCreateProductOpen] = useState(false);

  // Fetch brands
  const { data: brands, isLoading } = useQuery({
    queryKey: ["brands"],
    queryFn: brandApi.list,
  });

  // Fetch selected brand details
  const { data: selectedBrand } = useQuery({
    queryKey: ["brand", selectedBrandId],
    queryFn: () => brandApi.get(selectedBrandId!),
    enabled: !!selectedBrandId,
  });

  // Delete brand mutation
  const deleteBrandMutation = useMutation({
    mutationFn: brandApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brands"] });
      setSelectedBrandId(null);
    },
  });

  const handleDeleteBrand = (brandId: string) => {
    if (confirm("이 브랜드와 모든 제품을 삭제하시겠습니까?")) {
      deleteBrandMutation.mutate(brandId);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">브랜드 관리</h1>
          <p className="mt-2 text-muted">
            브랜드와 제품 정보를 등록하고 관리합니다.
          </p>
        </div>
        <button
          onClick={() => setIsCreateBrandOpen(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          브랜드 추가
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Brand List */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Building2 className="w-5 h-5" />
              브랜드 목록
            </h2>

            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted" />
              </div>
            ) : brands?.length === 0 ? (
              <div className="text-center py-8 text-muted">
                <Building2 className="w-12 h-12 mx-auto mb-2 opacity-30" />
                <p>등록된 브랜드가 없습니다.</p>
                <button
                  onClick={() => setIsCreateBrandOpen(true)}
                  className="mt-2 text-orange-500 hover:text-orange-400"
                >
                  첫 브랜드 추가하기
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {brands?.map((brand) => (
                  <button
                    key={brand.id}
                    onClick={() => setSelectedBrandId(brand.id)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedBrandId === brand.id
                        ? "border-orange-500 bg-orange-500/10 dark:bg-orange-500/20"
                        : "border-[rgb(var(--border))] hover:border-[rgb(var(--muted-foreground)/0.3)] hover:bg-[rgb(var(--muted)/0.5)]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-foreground">{brand.name}</p>
                        <p className="text-sm text-muted">
                          제품 {brand.product_count}개
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-muted" />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Brand Details */}
        <div className="lg:col-span-2">
          {selectedBrand ? (
            <div className="space-y-6">
              {/* Brand Info Card */}
              <div className="card">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-bold text-foreground">
                      {selectedBrand.name}
                    </h2>
                    {selectedBrand.industry && (
                      <span className="inline-block mt-1 px-2 py-0.5 bg-[rgb(var(--muted))] text-muted text-sm rounded">
                        {selectedBrand.industry}
                      </span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setIsEditBrandOpen(true)}
                      className="p-2 text-muted hover:text-foreground hover:bg-[rgb(var(--muted))] rounded-lg transition-colors"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteBrand(selectedBrand.id)}
                      className="p-2 text-red-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {selectedBrand.description && (
                  <p className="text-muted mb-4">{selectedBrand.description}</p>
                )}

                <div className="grid grid-cols-2 gap-4">
                  {selectedBrand.target_audience && (
                    <div className="flex items-start gap-2">
                      <Users className="w-4 h-4 text-muted mt-0.5" />
                      <div>
                        <p className="text-xs text-muted">타겟 고객</p>
                        <p className="text-sm text-foreground">{selectedBrand.target_audience}</p>
                      </div>
                    </div>
                  )}
                  {selectedBrand.tone_and_manner && (
                    <div className="flex items-start gap-2">
                      <Sparkles className="w-4 h-4 text-muted mt-0.5" />
                      <div>
                        <p className="text-xs text-muted">톤앤매너</p>
                        <p className="text-sm text-foreground">{selectedBrand.tone_and_manner}</p>
                      </div>
                    </div>
                  )}
                  {selectedBrand.usp && (
                    <div className="col-span-2 flex items-start gap-2">
                      <Tag className="w-4 h-4 text-muted mt-0.5" />
                      <div>
                        <p className="text-xs text-muted">USP (핵심 차별점)</p>
                        <p className="text-sm text-foreground">{selectedBrand.usp}</p>
                      </div>
                    </div>
                  )}
                </div>

                {selectedBrand.keywords?.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-1">
                    {selectedBrand.keywords.map((keyword, i) => (
                      <span
                        key={i}
                        className="badge badge-accent"
                      >
                        #{keyword}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Products Card */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                    <Package className="w-5 h-5" />
                    제품 목록
                  </h3>
                  <button
                    onClick={() => setIsCreateProductOpen(true)}
                    className="btn-secondary flex items-center gap-1 text-sm"
                  >
                    <Plus className="w-4 h-4" />
                    제품 추가
                  </button>
                </div>

                {selectedBrand.products.length === 0 ? (
                  <div className="text-center py-8 text-muted">
                    <Package className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>등록된 제품이 없습니다.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {selectedBrand.products.map((product) => (
                      <ProductCard
                        key={product.id}
                        product={product}
                        brandId={selectedBrand.id}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="text-center py-12 text-muted">
                <Building2 className="w-16 h-16 mx-auto mb-4 opacity-30" />
                <p className="text-lg">브랜드를 선택하세요</p>
                <p className="text-sm mt-1">
                  왼쪽 목록에서 브랜드를 선택하면 상세 정보를 볼 수 있습니다.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Brand Modal */}
      {isCreateBrandOpen && (
        <BrandFormModal
          onClose={() => setIsCreateBrandOpen(false)}
          onSuccess={(brand) => {
            setSelectedBrandId(brand.id);
            setIsCreateBrandOpen(false);
          }}
        />
      )}

      {/* Edit Brand Modal */}
      {isEditBrandOpen && selectedBrand && (
        <BrandFormModal
          brand={selectedBrand}
          onClose={() => setIsEditBrandOpen(false)}
          onSuccess={() => setIsEditBrandOpen(false)}
        />
      )}

      {/* Create Product Modal */}
      {isCreateProductOpen && selectedBrand && (
        <ProductFormModal
          brandId={selectedBrand.id}
          onClose={() => setIsCreateProductOpen(false)}
          onSuccess={() => setIsCreateProductOpen(false)}
        />
      )}
    </div>
  );
}

// ========== Constants for Cosmetics Labels ==========

const PRODUCT_CATEGORY_LABELS: Record<ProductCategory, string> = {
  serum: "세럼",
  cream: "크림",
  toner: "토너",
  essence: "에센스",
  oil: "오일",
  mask: "마스크",
  cleanser: "클렌저",
  sunscreen: "선크림",
  moisturizer: "모이스처라이저",
  eye_care: "아이케어",
  lip_care: "립케어",
  mist: "미스트",
  ampoule: "앰플",
  lotion: "로션",
  emulsion: "에멀전",
  balm: "밤",
  gel: "젤",
  foam: "폼",
  shampoo: "샴푸",
  conditioner: "컨디셔너",
  treatment: "트리트먼트",
  other: "기타",
};

const SKIN_TYPE_LABELS: Record<SkinType, string> = {
  dry: "건성",
  oily: "지성",
  combination: "복합성",
  normal: "중성",
  sensitive: "민감성",
  all: "모든 피부",
};

const SKIN_CONCERN_LABELS: Record<SkinConcern, string> = {
  acne: "여드름",
  pores: "모공",
  wrinkles: "주름",
  fine_lines: "잔주름",
  dark_spots: "기미",
  pigmentation: "색소침착",
  dullness: "칙칙함",
  redness: "홍조",
  dryness: "건조함",
  oiliness: "유분기",
  sagging: "처짐",
  elasticity: "탄력",
  uneven_tone: "피부톤",
  dark_circles: "다크서클",
  sensitivity: "민감함",
  dehydration: "수분부족",
  blackheads: "블랙헤드",
  whiteheads: "화이트헤드",
  aging: "노화",
  sun_damage: "자외선손상",
  texture: "피부결",
  barrier_damage: "장벽손상",
  hair_loss: "탈모",
  dandruff: "비듬",
  scalp_trouble: "두피트러블",
  other: "기타",
};

const INGREDIENT_CATEGORY_LABELS: Record<IngredientCategory, string> = {
  active: "활성성분",
  moisturizing: "보습",
  soothing: "진정",
  antioxidant: "항산화",
  exfoliant: "각질제거",
  brightening: "미백",
  firming: "탄력",
  barrier: "장벽강화",
  anti_aging: "안티에이징",
  hydrating: "수분",
  cleansing: "클렌징",
  other: "기타",
};

const TEXTURE_TYPE_LABELS: Record<TextureType, string> = {
  cream: "크림",
  gel: "젤",
  serum: "세럼",
  oil: "오일",
  water: "워터",
  milk: "밀크",
  balm: "밤",
  foam: "폼",
  mousse: "무스",
  mist: "미스트",
  powder: "파우더",
  stick: "스틱",
  sheet: "시트",
  patch: "패치",
  other: "기타",
};

const FINISH_TYPE_LABELS: Record<FinishType, string> = {
  matte: "매트",
  dewy: "글로우",
  satin: "새틴",
  natural: "내추럴",
  luminous: "광채",
  velvet: "벨벳",
  glossy: "글로시",
  invisible: "투명",
};

// ========== Product Card Component ==========

function ProductCard({ product, brandId }: { product: Product; brandId: string }) {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useState<HTMLInputElement | null>(null);

  const deleteMutation = useMutation({
    mutationFn: () => brandApi.deleteProduct(brandId, product.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brand", brandId] });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => brandApi.uploadProductImage(brandId, product.id, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brand", brandId] });
      setIsUploading(false);
    },
    onError: (error) => {
      console.error("Image upload failed:", error);
      setIsUploading(false);
    },
  });

  const handleDelete = () => {
    if (confirm("이 제품을 삭제하시겠습니까?")) {
      deleteMutation.mutate();
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setIsUploading(true);
      uploadMutation.mutate(file);
    }
  };

  // Get hero ingredients
  const heroIngredients = product.key_ingredients?.filter((ing) => ing.is_hero) || [];

  return (
    <>
      <div className="border border-[rgb(var(--border))] rounded-lg p-4 bg-[rgb(var(--card))]">
        <div className="flex gap-4">
          {/* Product Image */}
          <div className="flex-shrink-0">
            <div className="w-20 h-20 bg-[rgb(var(--muted))] rounded-lg overflow-hidden relative group">
              {isUploading || uploadMutation.isPending ? (
                <div className="absolute inset-0 flex items-center justify-center bg-[rgb(var(--muted))]">
                  <Loader2 className="w-6 h-6 text-orange-500 animate-spin" />
                </div>
              ) : product.image_url ? (
                <>
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                  <label className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer flex items-center justify-center">
                    <Upload className="w-5 h-5 text-white" />
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handleImageUpload}
                      className="hidden"
                    />
                  </label>
                </>
              ) : (
                <label className="absolute inset-0 flex flex-col items-center justify-center cursor-pointer hover:bg-[rgb(var(--muted)/0.8)] transition-colors">
                  <ImageIcon className="w-6 h-6 text-muted" />
                  <span className="text-xs text-muted mt-1">업로드</span>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleImageUpload}
                    className="hidden"
                  />
                </label>
              )}
            </div>
            {product.image_description && (
              <p className="text-xs text-muted mt-1 w-20 line-clamp-2" title={product.image_description}>
                AI 분석 완료
              </p>
            )}
          </div>

          {/* Product Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="font-medium text-foreground">{product.name}</h4>
              {product.product_category && (
                <span className="badge badge-purple">
                  {PRODUCT_CATEGORY_LABELS[product.product_category]}
                </span>
              )}
              {product.volume_ml && (
                <span className="text-xs text-muted">{product.volume_ml}ml</span>
              )}
            </div>
            {product.description && (
              <p className="text-sm text-muted mt-1">{product.description}</p>
            )}

            <div className="mt-3 space-y-2">
              {/* Hero Ingredients */}
              {heroIngredients.length > 0 && (
                <div>
                  <p className="text-xs text-muted flex items-center gap-1">
                    <Beaker className="w-3 h-3" />
                    히어로 성분
                  </p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {heroIngredients.map((ing, i) => (
                      <span
                        key={i}
                        className="text-xs bg-amber-500/15 text-amber-600 dark:text-amber-400 px-2 py-0.5 rounded border border-amber-500/20"
                        title={ing.effect}
                      >
                        <Star className="w-3 h-3 inline mr-1" />
                        {ing.name_ko || ing.name}
                        {ing.concentration && ` (${ing.concentration})`}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Skin Types */}
              {product.suitable_skin_types?.length > 0 && (
                <div>
                  <p className="text-xs text-muted flex items-center gap-1">
                    <Droplets className="w-3 h-3" />
                    적합 피부 타입
                  </p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {product.suitable_skin_types.map((type, i) => (
                      <span key={i} className="badge badge-cyan">
                        {SKIN_TYPE_LABELS[type]}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Texture & Finish */}
              {(product.texture_type || product.finish_type) && (
                <div className="flex gap-2">
                  {product.texture_type && (
                    <span className="text-xs bg-[rgb(var(--muted))] text-muted px-2 py-0.5 rounded">
                      텍스처: {TEXTURE_TYPE_LABELS[product.texture_type]}
                    </span>
                  )}
                  {product.finish_type && (
                    <span className="text-xs bg-[rgb(var(--muted))] text-muted px-2 py-0.5 rounded">
                      마무리감: {FINISH_TYPE_LABELS[product.finish_type]}
                    </span>
                  )}
                </div>
              )}

              {product.features?.length > 0 && (
                <div>
                  <p className="text-xs text-muted">주요 기능</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {product.features.map((f, i) => (
                      <span key={i} className="text-xs bg-blue-500/15 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {product.benefits?.length > 0 && (
                <div>
                  <p className="text-xs text-muted">혜택</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {product.benefits.map((b, i) => (
                      <span key={i} className="badge badge-success">
                        {b}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-4 text-xs text-muted">
                {product.price_range && <span>가격대: {product.price_range}</span>}
                {product.target_segment && <span>타겟: {product.target_segment}</span>}
              </div>
            </div>
          </div>

          <div className="flex gap-1 ml-4">
            <button
              onClick={() => setIsEditing(true)}
              className="p-1.5 text-muted hover:text-foreground hover:bg-[rgb(var(--muted))] rounded transition-colors"
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleDelete}
              className="p-1.5 text-muted hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {isEditing && (
        <ProductFormModal
          brandId={brandId}
          product={product}
          onClose={() => setIsEditing(false)}
          onSuccess={() => setIsEditing(false)}
        />
      )}
    </>
  );
}

// ========== Brand Form Modal ==========

function BrandFormModal({
  brand,
  onClose,
  onSuccess,
}: {
  brand?: Brand;
  onClose: () => void;
  onSuccess: (brand: Brand) => void;
}) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<BrandCreate>({
    name: brand?.name || "",
    description: brand?.description || "",
    target_audience: brand?.target_audience || "",
    tone_and_manner: brand?.tone_and_manner || "",
    usp: brand?.usp || "",
    keywords: brand?.keywords || [],
    industry: brand?.industry || "",
  });
  const [keywordInput, setKeywordInput] = useState("");

  const createMutation = useMutation({
    mutationFn: brandApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["brands"] });
      onSuccess(data);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: BrandCreate) => brandApi.update(brand!.id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["brands"] });
      queryClient.invalidateQueries({ queryKey: ["brand", brand!.id] });
      onSuccess(data);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (brand) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  const addKeyword = () => {
    if (keywordInput.trim() && !formData.keywords?.includes(keywordInput.trim())) {
      setFormData({
        ...formData,
        keywords: [...(formData.keywords || []), keywordInput.trim()],
      });
      setKeywordInput("");
    }
  };

  const removeKeyword = (keyword: string) => {
    setFormData({
      ...formData,
      keywords: formData.keywords?.filter((k) => k !== keyword),
    });
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-[rgb(var(--card))] rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto m-4 border border-[rgb(var(--border))]">
        <div className="flex items-center justify-between p-4 border-b border-[rgb(var(--border))]">
          <h2 className="text-lg font-semibold text-foreground">
            {brand ? "브랜드 수정" : "새 브랜드 추가"}
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-[rgb(var(--muted))] rounded transition-colors">
            <X className="w-5 h-5 text-muted" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              브랜드명 *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input w-full"
              placeholder="예: 삼성전자"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              설명
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="input w-full"
              rows={2}
              placeholder="브랜드에 대한 간략한 설명"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              업종
            </label>
            <input
              type="text"
              value={formData.industry}
              onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
              className="input w-full"
              placeholder="예: IT, 뷰티, 식품, 패션"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              타겟 고객층
            </label>
            <input
              type="text"
              value={formData.target_audience}
              onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
              className="input w-full"
              placeholder="예: 20-30대 직장인 여성"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              톤앤매너
            </label>
            <select
              value={formData.tone_and_manner}
              onChange={(e) => setFormData({ ...formData, tone_and_manner: e.target.value })}
              className="input w-full"
            >
              <option value="">선택하세요</option>
              <option value="전문적">전문적</option>
              <option value="친근한">친근한</option>
              <option value="캐주얼">캐주얼</option>
              <option value="고급스러운">고급스러운</option>
              <option value="유머러스">유머러스</option>
              <option value="감성적">감성적</option>
              <option value="신뢰감있는">신뢰감있는</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              USP (핵심 차별점)
            </label>
            <textarea
              value={formData.usp}
              onChange={(e) => setFormData({ ...formData, usp: e.target.value })}
              className="input w-full"
              rows={2}
              placeholder="경쟁사 대비 우리 브랜드만의 핵심 차별점"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              브랜드 키워드
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addKeyword())}
                className="input flex-1"
                placeholder="키워드 입력 후 Enter"
              />
              <button
                type="button"
                onClick={addKeyword}
                className="btn-secondary"
              >
                추가
              </button>
            </div>
            {formData.keywords && formData.keywords.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {formData.keywords.map((keyword, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 badge badge-accent"
                  >
                    #{keyword}
                    <button
                      type="button"
                      onClick={() => removeKeyword(keyword)}
                      className="hover:text-orange-300"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-[rgb(var(--border))]">
            <button type="button" onClick={onClose} className="btn-secondary">
              취소
            </button>
            <button type="submit" disabled={isLoading} className="btn-primary">
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : brand ? (
                "수정"
              ) : (
                "추가"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ========== Product Form Modal ==========

// Product category options
const PRODUCT_CATEGORIES: ProductCategory[] = [
  "serum", "cream", "toner", "essence", "oil", "mask", "cleanser",
  "sunscreen", "moisturizer", "eye_care", "lip_care", "mist", "ampoule",
  "lotion", "emulsion", "balm", "gel", "foam", "shampoo", "conditioner",
  "treatment", "other",
];

const SKIN_TYPES: SkinType[] = ["dry", "oily", "combination", "normal", "sensitive", "all"];

const SKIN_CONCERNS: SkinConcern[] = [
  "acne", "pores", "wrinkles", "fine_lines", "dark_spots", "pigmentation",
  "dullness", "redness", "dryness", "oiliness", "sagging", "elasticity",
  "uneven_tone", "dark_circles", "sensitivity", "dehydration", "blackheads",
  "whiteheads", "aging", "sun_damage", "texture", "barrier_damage",
  "hair_loss", "dandruff", "scalp_trouble", "other",
];

const INGREDIENT_CATEGORIES: IngredientCategory[] = [
  "active", "moisturizing", "soothing", "antioxidant", "exfoliant",
  "brightening", "firming", "barrier", "anti_aging", "hydrating",
  "cleansing", "other",
];

const TEXTURE_TYPES: TextureType[] = [
  "cream", "gel", "serum", "oil", "water", "milk", "balm", "foam",
  "mousse", "mist", "powder", "stick", "sheet", "patch", "other",
];

const FINISH_TYPES: FinishType[] = [
  "matte", "dewy", "satin", "natural", "luminous", "velvet", "glossy", "invisible",
];

function ProductFormModal({
  brandId,
  product,
  onClose,
  onSuccess,
}: {
  brandId: string;
  product?: Product;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"basic" | "ingredients" | "skin" | "texture">("basic");
  const [showLegacy, setShowLegacy] = useState(false);
  const [skinConcernSearch, setSkinConcernSearch] = useState("");

  const [formData, setFormData] = useState<ProductCreate>({
    name: product?.name || "",
    description: product?.description || "",
    features: product?.features || [],
    benefits: product?.benefits || [],
    price_range: product?.price_range || "",
    target_segment: product?.target_segment || "",
    // Cosmetics fields
    product_category: product?.product_category,
    key_ingredients: product?.key_ingredients || [],
    suitable_skin_types: product?.suitable_skin_types || [],
    skin_concerns: product?.skin_concerns || [],
    texture_type: product?.texture_type,
    finish_type: product?.finish_type,
    volume_ml: product?.volume_ml,
  });

  const [featureInput, setFeatureInput] = useState("");
  const [benefitInput, setBenefitInput] = useState("");

  // New ingredient form state
  const [newIngredient, setNewIngredient] = useState<Ingredient>({
    name: "",
    name_ko: "",
    effect: "",
    category: undefined,
    concentration: "",
    is_hero: false,
  });

  const createMutation = useMutation({
    mutationFn: (data: ProductCreate) => brandApi.createProduct(brandId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brand", brandId] });
      onSuccess();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: ProductCreate) => brandApi.updateProduct(brandId, product!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brand", brandId] });
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (product) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  // Feature handlers
  const addFeature = () => {
    if (featureInput.trim() && !formData.features?.includes(featureInput.trim())) {
      setFormData({
        ...formData,
        features: [...(formData.features || []), featureInput.trim()],
      });
      setFeatureInput("");
    }
  };

  const removeFeature = (feature: string) => {
    setFormData({
      ...formData,
      features: formData.features?.filter((f) => f !== feature),
    });
  };

  // Benefit handlers
  const addBenefit = () => {
    if (benefitInput.trim() && !formData.benefits?.includes(benefitInput.trim())) {
      setFormData({
        ...formData,
        benefits: [...(formData.benefits || []), benefitInput.trim()],
      });
      setBenefitInput("");
    }
  };

  const removeBenefit = (benefit: string) => {
    setFormData({
      ...formData,
      benefits: formData.benefits?.filter((b) => b !== benefit),
    });
  };

  // Ingredient handlers
  const addIngredient = () => {
    if (newIngredient.name.trim() && newIngredient.effect.trim()) {
      setFormData({
        ...formData,
        key_ingredients: [...(formData.key_ingredients || []), { ...newIngredient }],
      });
      setNewIngredient({
        name: "",
        name_ko: "",
        effect: "",
        category: undefined,
        concentration: "",
        is_hero: false,
      });
    }
  };

  const removeIngredient = (index: number) => {
    setFormData({
      ...formData,
      key_ingredients: formData.key_ingredients?.filter((_, i) => i !== index),
    });
  };

  // Skin type handlers
  const toggleSkinType = (type: SkinType) => {
    const current = formData.suitable_skin_types || [];
    if (current.includes(type)) {
      setFormData({
        ...formData,
        suitable_skin_types: current.filter((t) => t !== type),
      });
    } else {
      setFormData({
        ...formData,
        suitable_skin_types: [...current, type],
      });
    }
  };

  // Skin concern handlers
  const toggleSkinConcern = (concern: SkinConcern) => {
    const current = formData.skin_concerns || [];
    if (current.includes(concern)) {
      setFormData({
        ...formData,
        skin_concerns: current.filter((c) => c !== concern),
      });
    } else {
      setFormData({
        ...formData,
        skin_concerns: [...current, concern],
      });
    }
  };

  // Filter skin concerns based on search
  const filteredConcerns = SKIN_CONCERNS.filter((concern) =>
    skinConcernSearch
      ? SKIN_CONCERN_LABELS[concern].toLowerCase().includes(skinConcernSearch.toLowerCase()) ||
        concern.toLowerCase().includes(skinConcernSearch.toLowerCase())
      : true
  );

  const isLoading = createMutation.isPending || updateMutation.isPending;

  const tabs = [
    { id: "basic" as const, label: "기본 정보" },
    { id: "ingredients" as const, label: "주요 성분" },
    { id: "skin" as const, label: "피부 적합성" },
    { id: "texture" as const, label: "텍스처/마무리감" },
  ];

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-[rgb(var(--card))] rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden m-4 flex flex-col border border-[rgb(var(--border))]">
        <div className="flex items-center justify-between p-4 border-b border-[rgb(var(--border))] shrink-0">
          <h2 className="text-lg font-semibold text-foreground">
            {product ? "제품 수정" : "새 제품 추가"}
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-[rgb(var(--muted))] rounded transition-colors">
            <X className="w-5 h-5 text-muted" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[rgb(var(--border))] shrink-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "text-orange-500 border-b-2 border-orange-500 bg-orange-500/10"
                  : "text-muted hover:text-foreground hover:bg-[rgb(var(--muted)/0.5)]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Basic Info Tab */}
            {activeTab === "basic" && (
              <>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    제품명 *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input w-full"
                    placeholder="예: 히알루론산 수분 세럼"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      제품 카테고리
                    </label>
                    <select
                      value={formData.product_category || ""}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          product_category: (e.target.value || undefined) as ProductCategory | undefined,
                        })
                      }
                      className="input w-full"
                    >
                      <option value="">선택하세요</option>
                      {PRODUCT_CATEGORIES.map((cat) => (
                        <option key={cat} value={cat}>
                          {PRODUCT_CATEGORY_LABELS[cat]}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      용량 (ml)
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        min="0"
                        value={formData.volume_ml || ""}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            volume_ml: e.target.value ? parseInt(e.target.value) : undefined,
                          })
                        }
                        className="input w-full pr-10"
                        placeholder="50"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted text-sm">
                        ml
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    설명
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="input w-full"
                    rows={3}
                    placeholder="제품에 대한 간략한 설명"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    가격대
                  </label>
                  <input
                    type="text"
                    value={formData.price_range}
                    onChange={(e) => setFormData({ ...formData, price_range: e.target.value })}
                    className="input w-full"
                    placeholder="예: 3만원대"
                  />
                </div>
              </>
            )}

            {/* Ingredients Tab */}
            {activeTab === "ingredients" && (
              <>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="block text-sm font-medium text-foreground">
                      주요 성분
                    </label>
                    <span className="text-xs text-muted">
                      {formData.key_ingredients?.length || 0}개 등록됨
                    </span>
                  </div>

                  {/* Existing Ingredients */}
                  {formData.key_ingredients && formData.key_ingredients.length > 0 && (
                    <div className="space-y-2">
                      {formData.key_ingredients.map((ing, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border ${
                            ing.is_hero
                              ? "border-amber-500/30 bg-amber-500/10"
                              : "border-[rgb(var(--border))] bg-[rgb(var(--muted)/0.3)]"
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                {ing.is_hero && <Star className="w-4 h-4 text-amber-500" />}
                                <span className="font-medium text-foreground">{ing.name}</span>
                                {ing.name_ko && (
                                  <span className="text-sm text-muted">({ing.name_ko})</span>
                                )}
                                {ing.concentration && (
                                  <span className="text-xs bg-[rgb(var(--muted))] text-muted px-1.5 py-0.5 rounded">
                                    {ing.concentration}
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-muted mt-1">{ing.effect}</p>
                              {ing.category && (
                                <span className="inline-block mt-1 badge badge-accent">
                                  {INGREDIENT_CATEGORY_LABELS[ing.category]}
                                </span>
                              )}
                            </div>
                            <button
                              type="button"
                              onClick={() => removeIngredient(index)}
                              className="p-1 text-muted hover:text-red-500 transition-colors"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Add New Ingredient Form */}
                  <div className="border border-dashed border-[rgb(var(--border))] rounded-lg p-4 space-y-3">
                    <p className="text-sm font-medium text-foreground flex items-center gap-2">
                      <Beaker className="w-4 h-4" />
                      새 성분 추가
                    </p>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-muted mb-1">성분명 *</label>
                        <input
                          type="text"
                          value={newIngredient.name}
                          onChange={(e) =>
                            setNewIngredient({ ...newIngredient, name: e.target.value })
                          }
                          className="input w-full text-sm"
                          placeholder="예: Hyaluronic Acid"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-muted mb-1">한글명</label>
                        <input
                          type="text"
                          value={newIngredient.name_ko || ""}
                          onChange={(e) =>
                            setNewIngredient({ ...newIngredient, name_ko: e.target.value })
                          }
                          className="input w-full text-sm"
                          placeholder="예: 히알루론산"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs text-muted mb-1">효능 *</label>
                      <textarea
                        value={newIngredient.effect}
                        onChange={(e) =>
                          setNewIngredient({ ...newIngredient, effect: e.target.value })
                        }
                        className="input w-full text-sm"
                        rows={2}
                        placeholder="예: 피부 수분 공급 및 보습막 형성"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-muted mb-1">성분 카테고리</label>
                        <select
                          value={newIngredient.category || ""}
                          onChange={(e) =>
                            setNewIngredient({
                              ...newIngredient,
                              category: (e.target.value || undefined) as IngredientCategory | undefined,
                            })
                          }
                          className="input w-full text-sm"
                        >
                          <option value="">선택하세요</option>
                          {INGREDIENT_CATEGORIES.map((cat) => (
                            <option key={cat} value={cat}>
                              {INGREDIENT_CATEGORY_LABELS[cat]}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs text-muted mb-1">함량</label>
                        <input
                          type="text"
                          value={newIngredient.concentration || ""}
                          onChange={(e) =>
                            setNewIngredient({ ...newIngredient, concentration: e.target.value })
                          }
                          className="input w-full text-sm"
                          placeholder="예: 2%"
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={newIngredient.is_hero}
                          onChange={(e) =>
                            setNewIngredient({ ...newIngredient, is_hero: e.target.checked })
                          }
                          className="w-4 h-4 rounded border-[rgb(var(--border))] text-amber-500 focus:ring-amber-500 bg-[rgb(var(--muted))]"
                        />
                        <span className="text-sm text-foreground flex items-center gap-1">
                          <Star className="w-3.5 h-3.5 text-amber-500" />
                          히어로 성분
                        </span>
                      </label>

                      <button
                        type="button"
                        onClick={addIngredient}
                        disabled={!newIngredient.name.trim() || !newIngredient.effect.trim()}
                        className="btn-secondary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Plus className="w-4 h-4 mr-1" />
                        성분 추가
                      </button>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Skin Tab */}
            {activeTab === "skin" && (
              <>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                    <Droplets className="w-4 h-4" />
                    적합 피부 타입
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {SKIN_TYPES.map((type) => (
                      <button
                        key={type}
                        type="button"
                        onClick={() => toggleSkinType(type)}
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          formData.suitable_skin_types?.includes(type)
                            ? "bg-cyan-500 text-white"
                            : "bg-[rgb(var(--muted))] text-foreground hover:bg-[rgb(var(--muted)/0.8)]"
                        }`}
                      >
                        {SKIN_TYPE_LABELS[type]}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    피부 고민
                  </label>
                  <input
                    type="text"
                    value={skinConcernSearch}
                    onChange={(e) => setSkinConcernSearch(e.target.value)}
                    className="input w-full mb-3"
                    placeholder="피부 고민 검색..."
                  />

                  {/* Selected concerns */}
                  {formData.skin_concerns && formData.skin_concerns.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs text-muted mb-1">선택된 피부 고민:</p>
                      <div className="flex flex-wrap gap-1">
                        {formData.skin_concerns.map((concern) => (
                          <span
                            key={concern}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-rose-500/15 text-rose-600 dark:text-rose-400 text-sm rounded"
                          >
                            {SKIN_CONCERN_LABELS[concern]}
                            <button
                              type="button"
                              onClick={() => toggleSkinConcern(concern)}
                              className="hover:text-rose-300"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="max-h-48 overflow-y-auto border border-[rgb(var(--border))] rounded-lg p-2 bg-[rgb(var(--muted)/0.3)]">
                    <div className="flex flex-wrap gap-1">
                      {filteredConcerns.map((concern) => (
                        <button
                          key={concern}
                          type="button"
                          onClick={() => toggleSkinConcern(concern)}
                          className={`px-2 py-1 rounded text-sm transition-colors ${
                            formData.skin_concerns?.includes(concern)
                              ? "bg-rose-500 text-white"
                              : "bg-[rgb(var(--muted))] text-foreground hover:bg-[rgb(var(--muted)/0.8)]"
                          }`}
                        >
                          {SKIN_CONCERN_LABELS[concern]}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Texture Tab */}
            {activeTab === "texture" && (
              <>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    텍스처
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {TEXTURE_TYPES.map((type) => (
                      <button
                        key={type}
                        type="button"
                        onClick={() =>
                          setFormData({
                            ...formData,
                            texture_type: formData.texture_type === type ? undefined : type,
                          })
                        }
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          formData.texture_type === type
                            ? "bg-indigo-500 text-white"
                            : "bg-[rgb(var(--muted))] text-foreground hover:bg-[rgb(var(--muted)/0.8)]"
                        }`}
                      >
                        {TEXTURE_TYPE_LABELS[type]}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    마무리감
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {FINISH_TYPES.map((type) => (
                      <button
                        key={type}
                        type="button"
                        onClick={() =>
                          setFormData({
                            ...formData,
                            finish_type: formData.finish_type === type ? undefined : type,
                          })
                        }
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          formData.finish_type === type
                            ? "bg-violet-500 text-white"
                            : "bg-[rgb(var(--muted))] text-foreground hover:bg-[rgb(var(--muted)/0.8)]"
                        }`}
                      >
                        {FINISH_TYPE_LABELS[type]}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Legacy Section (Collapsible) */}
            <div className="border-t border-[rgb(var(--border))] pt-4 mt-4">
              <button
                type="button"
                onClick={() => setShowLegacy(!showLegacy)}
                className="flex items-center gap-2 text-sm text-muted hover:text-foreground transition-colors"
              >
                {showLegacy ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
                기존 필드 (기능, 혜택, 타겟 세그먼트)
              </button>

              {showLegacy && (
                <div className="mt-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      주요 기능/특징
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={featureInput}
                        onChange={(e) => setFeatureInput(e.target.value)}
                        onKeyDown={(e) =>
                          e.key === "Enter" && (e.preventDefault(), addFeature())
                        }
                        className="input flex-1"
                        placeholder="기능 입력 후 Enter"
                      />
                      <button type="button" onClick={addFeature} className="btn-secondary">
                        추가
                      </button>
                    </div>
                    {formData.features && formData.features.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {formData.features.map((feature, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-500/15 text-blue-600 dark:text-blue-400 text-sm rounded"
                          >
                            {feature}
                            <button type="button" onClick={() => removeFeature(feature)} className="hover:text-blue-300">
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      고객 혜택
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={benefitInput}
                        onChange={(e) => setBenefitInput(e.target.value)}
                        onKeyDown={(e) =>
                          e.key === "Enter" && (e.preventDefault(), addBenefit())
                        }
                        className="input flex-1"
                        placeholder="혜택 입력 후 Enter"
                      />
                      <button type="button" onClick={addBenefit} className="btn-secondary">
                        추가
                      </button>
                    </div>
                    {formData.benefits && formData.benefits.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {formData.benefits.map((benefit, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1 badge badge-success"
                          >
                            {benefit}
                            <button type="button" onClick={() => removeBenefit(benefit)} className="hover:text-green-300">
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      타겟 세그먼트
                    </label>
                    <input
                      type="text"
                      value={formData.target_segment}
                      onChange={(e) =>
                        setFormData({ ...formData, target_segment: e.target.value })
                      }
                      className="input w-full"
                      placeholder="예: 프리미엄"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end gap-2 p-4 border-t border-[rgb(var(--border))] shrink-0 bg-[rgb(var(--card))]">
            <button type="button" onClick={onClose} className="btn-secondary">
              취소
            </button>
            <button type="submit" disabled={isLoading} className="btn-primary">
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : product ? (
                "수정"
              ) : (
                "추가"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
