package com.uoa.mobile

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Context
import android.os.Bundle
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private lateinit var urlInput: EditText
    private lateinit var loadButton: Button

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val preferences = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val savedUrl = preferences.getString(KEY_BACKEND_URL, DEFAULT_BACKEND_URL) ?: DEFAULT_BACKEND_URL

        urlInput = findViewById(R.id.backendUrlInput)
        loadButton = findViewById(R.id.loadBackendButton)
        webView = findViewById(R.id.mainWebView)

        urlInput.setText(savedUrl)

        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                return false
            }
        }

        loadButton.setOnClickListener {
            loadBackendUrl()
        }

        urlInput.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_DONE || actionId == EditorInfo.IME_ACTION_GO) {
                loadBackendUrl()
                true
            } else {
                false
            }
        }

        loadBackendUrl()
    }

    private fun loadBackendUrl() {
        val preferences = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val rawValue = urlInput.text?.toString()?.trim().orEmpty()
        var normalized = if (rawValue.isBlank()) DEFAULT_BACKEND_URL else rawValue

        if (!normalized.startsWith("http://") && !normalized.startsWith("https://")) {
            normalized = "http://$normalized"
        }
        if (!normalized.endsWith("/")) {
            normalized = "$normalized/"
        }

        preferences.edit().putString(KEY_BACKEND_URL, normalized).apply()
        urlInput.setText(normalized)
        urlInput.setSelection(normalized.length)
        webView.loadUrl(normalized)
        hideKeyboard()
    }

    private fun hideKeyboard() {
        val manager = getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager ?: return
        manager.hideSoftInputFromWindow(urlInput.windowToken, 0)
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    companion object {
        private const val PREFS_NAME = "uoa_mobile_prefs"
        private const val KEY_BACKEND_URL = "backend_url"
        private const val DEFAULT_BACKEND_URL = "http://10.0.2.2:8000/"
    }
}
