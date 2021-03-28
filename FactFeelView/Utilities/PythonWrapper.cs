using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace FactFeelUI.Utilities
{
    public static class PythonWrapper
    {
        public static void InvokeScript(string filePath, string args)
        {
            ProcessStartInfo processStartInfo = new ProcessStartInfo();
            processStartInfo.FileName = filePath;
            processStartInfo.Arguments = string.Format(args);
            processStartInfo.UseShellExecute = false;
            processStartInfo.RedirectStandardOutput = true;

            using (Process process = Process.Start(processStartInfo))
            using (StreamReader reader = process.StandardOutput)
            {
                //Grabs the output from the script execution
            }
        }
    }
}
