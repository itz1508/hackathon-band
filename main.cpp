#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include "backend.h"

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    
    // Initialize Python
    Py_Initialize();
    
    // Create backend
    Backend backend;
    
    // Create QML engine
    QQmlApplicationEngine engine;
    
    // Register backend with QML
    engine.rootContext()->setContextProperty("backend", &backend);
    
    // Load main QML
    const QUrl url(QStringLiteral("qrc:/frontend/main.qml"));
    engine.load(url);
    
    if (engine.rootObjects().isEmpty())
        return -1;
    
    int result = app.exec();
    
    // Finalize Python
    Py_Finalize();
    
    return result;
}
