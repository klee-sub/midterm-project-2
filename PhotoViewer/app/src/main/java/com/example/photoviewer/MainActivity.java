package com.example.photoviewer;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.LinearLayout;
import android.widget.Toast;
import androidx.activity.EdgeToEdge;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class MainActivity extends AppCompatActivity {
    private static final int PICK_IMAGE = 41;
    private static final String SITE_URL = "http://10.0.2.2:8000";
    private String authToken;
    private TextView textView;
    private String pendingTitle, pendingBody, pendingTags;
    private CloadImage taskDownload;
    private final Handler pollingHandler = new Handler(Looper.getMainLooper());
    private final Runnable pollingTask = new Runnable() {
        @Override
        public void run() {
            onClickDownload(null);
            pollingHandler.postDelayed(this, 10000);
        }
    };
    private SharedPreferences preferences;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        textView = findViewById(R.id.textView);
        preferences = getSharedPreferences("photo_viewer", Context.MODE_PRIVATE);
        authToken = preferences.getString("token", null);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (view, insets) -> {
            Insets bars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            return insets;
        });
        if (authToken == null) showLoginDialog();
        else startClient();
    }

    private void startClient() {
        onClickDownload(null);
        pollingHandler.removeCallbacks(pollingTask);
        pollingHandler.postDelayed(pollingTask, 10000);
    }

    public void onClickLogin(View view) {
        showLoginDialog();
    }

    private void showLoginDialog() {
        View v = getLayoutInflater().inflate(R.layout.dialog_login, null);
        EditText user = v.findViewById(R.id.loginUsername), pass = v.findViewById(R.id.loginPassword);
        new AlertDialog.Builder(this)
                .setTitle("로그인")
                .setView(v)
                .setNegativeButton("취소", null)
                .setPositiveButton("로그인", (d, w) -> new LoginTask().execute(
                        user.getText().toString().trim(),
                        pass.getText().toString()))
                .show();
    }

    @Override
    protected void onDestroy() {
        pollingHandler.removeCallbacks(pollingTask);
        super.onDestroy();
    }

    public void onClickDownload(View view) {
        if (taskDownload != null && taskDownload.getStatus() == AsyncTask.Status.RUNNING) taskDownload.cancel(true);
        taskDownload = new CloadImage();
        taskDownload.execute(SITE_URL + "/api_root/Post/");
    }

    public void onClickUpload(View view) {
        View v = getLayoutInflater().inflate(R.layout.dialog_post, null);
        EditText title = v.findViewById(R.id.dialogTitle),
                body = v.findViewById(R.id.dialogBody),
                tags = v.findViewById(R.id.dialogTags);
        new AlertDialog.Builder(this)
                .setTitle("새로운 이미지 게시")
                .setView(v)
                .setNegativeButton("취소", null)
                .setPositiveButton("이미지 선택", (d, w) -> {
                    pendingTitle = title.getText().toString().trim();
                    pendingBody = body.getText().toString().trim();
                    pendingTags = tags.getText().toString().trim();
                    if (pendingTitle.isEmpty() || pendingBody.isEmpty()) {
                        Toast.makeText(this, "제목과 본문을 모두 입력하세요.", Toast.LENGTH_LONG).show();
                        return;
                    }
                    Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("image/*");
                    startActivityForResult(i, PICK_IMAGE);
                })
                .show();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_IMAGE && resultCode == RESULT_OK && data != null && data.getData() != null)
            showImageEditor(data.getData());
    }

    private void showImageEditor(Uri uri) {
        try {
            Bitmap bitmap = BitmapFactory.decodeStream(getContentResolver().openInputStream(uri));
            if (bitmap == null) throw new IOException("이미지를 열 수 없습니다.");
            ImageView preview = new ImageView(this);
            preview.setImageBitmap(bitmap);
            preview.setAdjustViewBounds(true);
            final Bitmap[] edited = {bitmap};
            AlertDialog editor = new AlertDialog.Builder(this)
                    .setTitle("사진 수정")
                    .setView(preview)
                    .setNegativeButton("취소", null)
                    .setNeutralButton("회전", null)
                    .setPositiveButton("업로드", (d, w) -> new PutPost().execute(
                            new UploadRequest(edited[0], pendingTitle, pendingBody, pendingTags)))
                    .create();
            editor.setOnShowListener(dialog -> editor.getButton(AlertDialog.BUTTON_NEUTRAL)
                    .setOnClickListener(button -> {
                        edited[0] = rotate(edited[0]);
                        preview.setImageBitmap(edited[0]);
                    }));
            editor.show();
        } catch (Exception e) {
            Toast.makeText(this, e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private Bitmap rotate(Bitmap source) {
        Matrix matrix = new Matrix();
        matrix.postRotate(90);
        return Bitmap.createBitmap(source, 0, 0, source.getWidth(), source.getHeight(), matrix, true);
    }

    private String imageUrl(String value) {
        if (value.startsWith("http://127.0.0.1") || value.startsWith("http://localhost"))
            return value.replaceFirst("http://(?:127\\.0\\.0\\.1|localhost)", SITE_URL);
        if (value.startsWith("/")) return SITE_URL + value;
        return value;
    }

    private class LoginTask extends AsyncTask<String, Void, String> {
        private String error;

        @Override
        protected String doInBackground(String... values) {
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(SITE_URL + "/api-token-auth/").openConnection();
                c.setDoOutput(true);
                c.setRequestMethod("POST");
                c.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
                String form = "username=" + URLEncoder.encode(values[0], "UTF-8")
                        + "&password=" + URLEncoder.encode(values[1], "UTF-8");
                try (OutputStream o = c.getOutputStream()) {
                    o.write(form.getBytes(StandardCharsets.UTF_8));
                }
                if (c.getResponseCode() != 200) {
                    error = "아이디 또는 비밀번호가 올바르지 않습니다.";
                    return null;
                }
                return new JSONObject(read(c.getInputStream())).getString("token");
            } catch (Exception e) {
                error = e.getMessage();
                return null;
            }
        }

        @Override
        protected void onPostExecute(String token) {
            if (token == null) {
                Toast.makeText(MainActivity.this, error, Toast.LENGTH_LONG).show();
                return;
            }
            authToken = token;
            preferences.edit().putString("token", token).apply();
            findViewById(R.id.btn_login).setVisibility(View.GONE);
            startClient();
        }
    }

    private class CloadImage extends AsyncTask<String, Void, List<PostItem>> {
        private String error;

        @Override
        protected List<PostItem> doInBackground(String... urls) {
            List<PostItem> result = new ArrayList<>();
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(urls[0]).openConnection();
                addAuth(c);
                if (c.getResponseCode() != 200) {
                    error = "서버 응답 " + c.getResponseCode();
                    return result;
                }
                JSONArray posts = new JSONArray(read(c.getInputStream()));
                for (int i = 0; i < posts.length() && !isCancelled(); i++) {
                    JSONObject p = posts.getJSONObject(i);
                    String image = p.optString("image", "");
                    if (image.isEmpty()) continue;
                    HttpURLConnection ic = (HttpURLConnection) new URL(imageUrl(image)).openConnection();
                    addAuth(ic);
                    Bitmap b = BitmapFactory.decodeStream(ic.getInputStream());
                    List<String> tags = jsonStrings(p.optJSONArray("tags"));
                    List<String> comments = new ArrayList<>();
                    JSONArray cs = p.optJSONArray("comments");
                    if (cs != null)
                        for (int j = 0; j < cs.length(); j++)
                            comments.add(cs.getJSONObject(j).optString("author_name")
                                    + ": " + cs.getJSONObject(j).optString("text"));
                    if (b != null)
                        result.add(new PostItem(p.optInt("id"), b, p.optString("title"), p.optString("text"), tags, comments));
                    ic.disconnect();
                }
                c.disconnect();
            } catch (Exception e) {
                error = e.getMessage();
            }
            return result;
        }

        @Override
        protected void onPostExecute(List<PostItem> posts) {
            if (posts.isEmpty()) textView.setText(error == null ? "게시물이 없습니다." : "로드 실패: " + error);
            else {
                textView.setText("게시물 " + posts.size() + "개");
                RecyclerView r = findViewById(R.id.recyclerView);
                r.setLayoutManager(new LinearLayoutManager(MainActivity.this));
                r.setAdapter(new ImageAdapter(posts, MainActivity.this::showComments));
            }
        }
    }

    private void showComments(PostItem post) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(24, 8, 24, 0);
        TextView comments = new TextView(this);
        comments.setText(post.comments.isEmpty() ? "댓글이 없습니다." : String.join("\n", post.comments));
        EditText input = new EditText(this);
        input.setHint("댓글을 입력하세요");
        box.addView(comments);
        box.addView(input);
        new AlertDialog.Builder(this)
                .setTitle(post.title)
                .setView(box)
                .setNegativeButton("닫기", null)
                .setPositiveButton("댓글 등록", (d, w) -> {
                    String text = input.getText().toString().trim();
                    if (!text.isEmpty()) new CommentTask().execute(String.valueOf(post.id), text);
                })
                .show();
    }

    private class CommentTask extends AsyncTask<String, Void, Boolean> {
        @Override
        protected Boolean doInBackground(String... v) {
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(SITE_URL + "/api_root/Comment/").openConnection();
                c.setDoOutput(true);
                c.setRequestMethod("POST");
                c.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
                addAuth(c);
                String form = "post=" + URLEncoder.encode(v[0], "UTF-8")
                        + "&text=" + URLEncoder.encode(v[1], "UTF-8");
                try (OutputStream o = c.getOutputStream()) {
                    o.write(form.getBytes(StandardCharsets.UTF_8));
                }
                return c.getResponseCode() >= 200 && c.getResponseCode() < 300;
            } catch (Exception e) {
                return false;
            }
        }

        @Override
        protected void onPostExecute(Boolean ok) {
            Toast.makeText(MainActivity.this, ok ? "댓글을 등록했습니다." : "댓글 등록에 실패했습니다.", Toast.LENGTH_LONG).show();
            if (ok) onClickDownload(null);
        }
    }

    private class PutPost extends AsyncTask<UploadRequest, Void, Boolean> {
        private String message;

        @Override
        protected Boolean doInBackground(UploadRequest... values) {
            String boundary = "----PhotoViewer" + UUID.randomUUID();
            try {
                UploadRequest r = values[0];
                HttpURLConnection c = (HttpURLConnection) new URL(SITE_URL + "/api_root/Post/").openConnection();
                c.setDoOutput(true);
                c.setRequestMethod("POST");
                addAuth(c);
                c.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
                try (OutputStream o = c.getOutputStream()) {
                    part(o, boundary, "title", r.title);
                    part(o, boundary, "text", r.body);
                    part(o, boundary, "tags", r.tags);
                    part(o, boundary, "published_date",
                            new java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX").format(new java.util.Date()));
                    o.write(("--" + boundary + "\r\nContent-Disposition: form-data; name=\"image\"; filename=\"edited.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n")
                            .getBytes(StandardCharsets.UTF_8));
                    o.write(r.imageBytes());
                    o.write(("\r\n--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));
                }
                int code = c.getResponseCode();
                message = code >= 200 && code < 300 ? "게시했습니다." : "서버 응답 " + code;
                return code >= 200 && code < 300;
            } catch (Exception e) {
                message = e.getMessage();
                return false;
            }
        }

        private void part(OutputStream o, String b, String n, String v) throws IOException {
            o.write(("--" + b + "\r\nContent-Disposition: form-data; name=\"" + n + "\"\r\n\r\n" + (v == null ? "" : v) + "\r\n")
                    .getBytes(StandardCharsets.UTF_8));
        }

        @Override
        protected void onPostExecute(Boolean ok) {
            Toast.makeText(MainActivity.this, message, Toast.LENGTH_LONG).show();
            if (ok) onClickDownload(null);
        }
    }

    private static class UploadRequest {
        final Bitmap image;
        final String title, body, tags;

        UploadRequest(Bitmap image, String title, String body, String tags) {
            this.image = image;
            this.title = title;
            this.body = body;
            this.tags = tags;
        }

        byte[] imageBytes() {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            image.compress(Bitmap.CompressFormat.JPEG, 90, out);
            return out.toByteArray();
        }
    }

    private void addAuth(HttpURLConnection c) {
        if (authToken != null) c.setRequestProperty("Authorization", "Token " + authToken);
    }

    private List<String> jsonStrings(JSONArray a) throws Exception {
        List<String> out = new ArrayList<>();
        if (a != null)
            for (int i = 0; i < a.length(); i++)
                out.add(a.getString(i));
        return out;
    }

    private String read(InputStream in) throws IOException {
        StringBuilder s = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String l;
            while ((l = r.readLine()) != null)
                s.append(l);
        }
        return s.toString();
    }
}
