using IronPython.Hosting;
using Microsoft.Scripting.Hosting;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;

namespace FactFeelUI.Utilities
{
    public static class PythonWrapper
    {
        private static ScriptEngine pythonHost;

        public static void InvokeScript(string filePath, string args)
        {
            pythonHost = Python.CreateEngine();
            Listen();
        }

        private static void Listen()
        {
            //pythonHost.Runtime.ImportModule("TestClass");
            ICollection<string> searchPaths = pythonHost.GetSearchPaths();
            //searchPaths.Add(@"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python37_64\Lib\");
            //searchPaths.Add(@"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python37_64\Lib\site-packages\");
            //searchPaths.Add(@".\");
            //pythonHost.SetSearchPaths(searchPaths);
            dynamic clientScript = pythonHost.Runtime.UseFile("factfeelclient.py");
            string audioToText = clientScript.listen1();
            Debug.WriteLine(audioToText);
        }
    }
}
