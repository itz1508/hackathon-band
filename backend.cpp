#include "backend.h"
#include <QDebug>
#include <QJsonDocument>
#include <QJsonObject>

Backend::Backend(QObject *parent)
    : QObject(parent), pModule(nullptr), pBackendClass(nullptr), pBackendInstance(nullptr)
{
    initializePythonBackend();
}

Backend::~Backend()
{
    Py_XDECREF(pBackendInstance);
    Py_XDECREF(pBackendClass);
    Py_XDECREF(pModule);
}

void Backend::initializePythonBackend()
{
    // Add backend directory to Python path
    PyRun_SimpleString("import sys");
    PyRun_SimpleString("sys.path.append('./backend')");
    
    // Import the backend module
    PyObject *pName = PyUnicode_DecodeFSDefault("core");
    pModule = PyImport_Import(pName);
    Py_DECREF(pName);
    
    if (pModule != nullptr) {
        // Get the MVPBackend class
        pBackendClass = PyObject_GetAttrString(pModule, "MVPBackend");
        
        if (pBackendClass && PyCallable_Check(pBackendClass)) {
            // Create instance
            pBackendInstance = PyObject_CallObject(pBackendClass, nullptr);
        } else {
            emit error("Failed to load MVPBackend class");
        }
    } else {
        emit error("Failed to import core module");
    }
}

void Backend::startWorkflow(const QString &folderPath)
{
    if (!pBackendInstance) {
        emit error("Backend not initialized");
        return;
    }
    
    try {
        // Convert QString to Python string
        PyObject *pFolderPath = PyUnicode_FromString(folderPath.toStdString().c_str());
        
        // Call scan_folder
        PyObject *pScanMethod = PyObject_GetAttrString(pBackendInstance, "scan_folder");
        if (pScanMethod && PyCallable_Check(pScanMethod)) {
            PyObject *pScanResult = PyObject_CallFunctionObjArgs(pScanMethod, pFolderPath, nullptr);
            if (pScanResult) {
                emit scanCompleted(pythonObjectToVariant(pScanResult));
                Py_DECREF(pScanResult);
            }
            Py_DECREF(pScanMethod);
        }
        
        // Call create_plan
        PyObject *pPlanMethod = PyObject_GetAttrString(pBackendInstance, "create_plan");
        if (pPlanMethod && PyCallable_Check(pPlanMethod)) {
            PyObject *pScan = PyObject_GetAttrString(pBackendInstance, "current_scan");
            PyObject *pPlanResult = PyObject_CallFunctionObjArgs(pPlanMethod, pScan, nullptr);
            if (pPlanResult) {
                emit planCreated(pythonObjectToVariant(pPlanResult));
                Py_DECREF(pPlanResult);
            }
            Py_XDECREF(pScan);
            Py_DECREF(pPlanMethod);
        }
        
        // Call validate_plan
        PyObject *pValidateMethod = PyObject_GetAttrString(pBackendInstance, "validate_plan");
        if (pValidateMethod && PyCallable_Check(pValidateMethod)) {
            PyObject *pPlan = PyObject_GetAttrString(pBackendInstance, "current_plan");
            PyObject *pValidateResult = PyObject_CallFunctionObjArgs(pValidateMethod, pPlan, nullptr);
            if (pValidateResult) {
                emit validationCompleted(pythonObjectToVariant(pValidateResult));
                Py_DECREF(pValidateResult);
            }
            Py_XDECREF(pPlan);
            Py_DECREF(pValidateMethod);
        }
        
        // Call simulate_execution
        PyObject *pSimulateMethod = PyObject_GetAttrString(pBackendInstance, "simulate_execution");
        if (pSimulateMethod && PyCallable_Check(pSimulateMethod)) {
            PyObject *pPlan = PyObject_GetAttrString(pBackendInstance, "current_plan");
            PyObject *pSimulateResult = PyObject_CallFunctionObjArgs(pSimulateMethod, pPlan, pFolderPath, nullptr);
            if (pSimulateResult) {
                emit simulationCompleted(pythonObjectToVariant(pSimulateResult));
                Py_DECREF(pSimulateResult);
            }
            Py_XDECREF(pPlan);
            Py_DECREF(pSimulateMethod);
        }
        
        // Call generate_report
        PyObject *pReportMethod = PyObject_GetAttrString(pBackendInstance, "generate_report");
        if (pReportMethod && PyCallable_Check(pReportMethod)) {
            PyObject *pReportResult = PyObject_CallObject(pReportMethod, nullptr);
            if (pReportResult) {
                emit reportGenerated(pythonObjectToVariant(pReportResult));
                Py_DECREF(pReportResult);
            }
            Py_DECREF(pReportMethod);
        }
        
        Py_DECREF(pFolderPath);
        
    } catch (const std::exception &e) {
        emit error(QString::fromStdString(e.what()));
    }
}

QVariant Backend::pythonObjectToVariant(PyObject *obj)
{
    if (obj == nullptr) {
        return QVariant();
    }
    
    // Handle None
    if (obj == Py_None) {
        return QVariant();
    }
    
    // Handle bool
    if (PyBool_Check(obj)) {
        return QVariant(PyObject_IsTrue(obj) == 1);
    }
    
    // Handle int
    if (PyLong_Check(obj)) {
        return QVariant((qlonglong)PyLong_AsLong(obj));
    }
    
    // Handle float
    if (PyFloat_Check(obj)) {
        return QVariant(PyFloat_AsDouble(obj));
    }
    
    // Handle string
    if (PyUnicode_Check(obj)) {
        return QVariant(QString::fromUtf8(PyUnicode_AsUTF8(obj)));
    }
    
    // Handle dict - convert to JSON
    if (PyDict_Check(obj)) {
        PyObject *pJsonStr = PyObject_CallMethod(obj, "__str__", nullptr);
        if (pJsonStr) {
            QString jsonStr = QString::fromUtf8(PyUnicode_AsUTF8(pJsonStr));
            Py_DECREF(pJsonStr);
            return QVariant(jsonStr);
        }
    }
    
    // Handle list
    if (PyList_Check(obj)) {
        QVariantList list;
        for (Py_ssize_t i = 0; i < PyList_Size(obj); ++i) {
            list.append(pythonObjectToVariant(PyList_GetItem(obj, i)));
        }
        return QVariant(list);
    }
    
    // Default: convert to string
    PyObject *pStr = PyObject_Str(obj);
    if (pStr) {
        QString result = QString::fromUtf8(PyUnicode_AsUTF8(pStr));
        Py_DECREF(pStr);
        return QVariant(result);
    }
    
    return QVariant();
}
