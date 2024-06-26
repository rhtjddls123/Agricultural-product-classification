export type products = "cabbage" | "apple" | "radish"; // | "chinese_cabbage";

export type result = {
  predicted_percent: number[];
  predicted_class: 0 | 1 | 2;
  url: string;
};

export type kakao = {
  access_token: string;
  expires_in: number;
  refresh_token: string;
  refresh_koken_expires_in: number;
  scope: string;
  token_type: string;
};

export type kakaoLogin = {
  data: { user_email: string; user_name: string };
  result: string;
};

export type info = {
  efficacy: string;
  select_tip: string;
  standard: string;
};

export type saveLogin = {
  platform: string;
  refresh?: string;
  email?: string;
};

export type login = {
  platform: string;
  email: string;
};

export type resultType = {
  result_id: number;
  product_name: products;
  grade_id: 0 | 1 | 2;
  date: string;
  image_path: string;
};

export type profile = {
  name: string;
};

export type oc = {
  if_clf: 1 | -1;
  oc_svm: 1 | -1;
};
