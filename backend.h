#ifndef BACKEND_H
#define BACKEND_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <QObject>
#include <QString>
#include <QVariant>

class Backend : public QObject
{
    Q_OBJECT
    
public:
    explicit Backend(QObject *parent = nullptr);
    ~Backend();
    
    Q_INVOKABLE void startWorkflow(const QString &folderPath);
    
signals:
    void scanCompleted(const QVariant &result);
    void planCreated(const QVariant &plan);
    void validationCompleted(const QVariant &result);
    void simulationCompleted(const QVariant &result);
    void reportGenerated(const QVariant &report);
    void error(const QString &message);
    
private:
    PyObject *pModule;
    PyObject *pBackendClass;
    PyObject *pBackendInstance;
    
    QVariant pythonObjectToVariant(PyObject *obj);
    void initializePythonBackend();
};

#endif // BACKEND_H
