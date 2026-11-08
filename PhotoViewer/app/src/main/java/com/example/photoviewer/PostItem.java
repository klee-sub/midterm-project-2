package com.example.photoviewer;

import android.graphics.Bitmap;
import java.util.ArrayList;
import java.util.List;

public class PostItem {
    public final Bitmap image;
    public final String title;
    public final String text;
    public final List<String> tags;
    public final int id;
    public final List<String> comments;
    public PostItem(int id, Bitmap image, String title, String text, List<String> tags, List<String> comments) {
        this.id=id; this.image = image; this.title = title; this.text = text; this.tags = tags == null ? new ArrayList<>() : tags; this.comments = comments == null ? new ArrayList<>() : comments;
    }
}
